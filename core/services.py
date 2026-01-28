import asyncio
import json
import time
from django.utils import timezone

from .fetcher import fetch_final_url, extract_params
from .utils import build_final_suffix, extract_full_query
from .models import RunLog


def run_mapping(mapping):
    """
    Stateless.
    Every call generates:
    - fresh suffix
    - fresh RunLog
    """
    final_url = None
    extracted_map = None

    try:
        result = asyncio.run(fetch_final_url(mapping.tracking_url))
        final_url = result["final_url"]

        # -----------------------
        # PARAM EXTRACTION
        # -----------------------
        if mapping.extract_all_params:
            base_suffix = extract_full_query(final_url) or ""
        else:
            params = mapping.params or []
            if isinstance(params, str):
                params = json.loads(params)

            extracted_map = extract_params(final_url, params)
            base_suffix = build_final_suffix(extracted_map) if extracted_map else ""

        # -----------------------
        # 🔥 FORCE UNIQUENESS (CRITICAL)
        # -----------------------
        nonce = int(time.time() * 1000)

        if base_suffix:
            final_suffix = f"{base_suffix}&_ts={nonce}"
        else:
            # Even if affiliate blocks params, ALWAYS return something
            final_suffix = f"_ts={nonce}"

        # -----------------------
        # SAVE
        # -----------------------
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
            extracted_value=str(extracted_map),
            success=False,
            error_message=str(e),
        )
        raise
