import asyncio
import json
import logging
from django.utils import timezone

from .fetcher import fetch_final_url, extract_params
from .utils import extract_full_query
from .models import RunLog

logger = logging.getLogger(__name__)


def _build_suffix(mapping, final_url, index=0):
    if mapping.extract_all_params:
        return extract_full_query(final_url) or ""
    else:
        params = mapping.params or []
        if isinstance(params, str):
            params = json.loads(params)
        return extract_params(final_url, params)


def run_mapping(mapping):
    final_url = None

    try:
        result = asyncio.run(fetch_final_url(mapping.tracking_url))
        final_url = result["final_url"]
        final_suffix = _build_suffix(mapping, final_url)

        mapping.last_suffix = final_suffix
        mapping.last_run_at = timezone.now()
        mapping.save(update_fields=["last_suffix", "last_run_at", "updated_at"])

        RunLog.objects.create(
            mapping=mapping,
            final_url=final_url,
            extracted_value=final_suffix,
            success=True,
        )

        return final_suffix

    except Exception as e:
        RunLog.objects.create(
            mapping=mapping,
            final_url=final_url,
            extracted_value=None,
            success=False,
            error_message=str(e),
        )
        raise


def run_mapping_batch(mapping, count):
    async def _fetch_one(index):
        result = await fetch_final_url(mapping.tracking_url)
        final_url = result["final_url"]
        suffix = _build_suffix(mapping, final_url, index)
        logger.info(
            "Batch item #%d | tracking_url=%s | final_url=%s | suffix='%s'",
            index, mapping.tracking_url, final_url, suffix,
        )
        return {"suffix": suffix, "final_url": final_url}

    async def _batch():
        sem = asyncio.Semaphore(10)

        async def _limited(i):
            async with sem:
                return await _fetch_one(i)

        return await asyncio.gather(
            *[_limited(i) for i in range(count)],
            return_exceptions=True,
        )

    results = asyncio.run(_batch())

    suffixes = []
    errors = []
    debug_urls = []

    for r in results:
        if isinstance(r, Exception):
            errors.append(str(r))
            logger.warning("Batch fetch error: %s", r)
            RunLog.objects.create(
                mapping=mapping, success=False, error_message=str(r),
            )
        else:
            debug_urls.append(r["final_url"])
            if r["suffix"]:  # skip empty suffixes
                suffixes.append(r["suffix"])
                RunLog.objects.create(
                    mapping=mapping,
                    final_url=r["final_url"],
                    extracted_value=r["suffix"],
                    success=True,
                )
            else:
                errors.append(f"empty_suffix from {r['final_url']}")
                logger.warning("Empty suffix from final_url=%s", r["final_url"])
                RunLog.objects.create(
                    mapping=mapping,
                    final_url=r["final_url"],
                    extracted_value="",
                    success=False,
                    error_message=f"Empty suffix extracted from {r['final_url']}",
                )

    logger.info(
        "Batch complete: config=%s | suffixes=%d | errors=%d",
        mapping.config_name, len(suffixes), len(errors),
    )

    if suffixes:
        mapping.last_suffix = suffixes[-1]
        mapping.last_run_at = timezone.now()
        mapping.save(update_fields=["last_suffix", "last_run_at", "updated_at"])

    return suffixes, errors
