import asyncio
import base64
import json
from pathlib import Path

import nodriver as uc
from nodriver import cdp


CDP_HOST = "127.0.0.1"
CDP_PORT = 9223

ICE_REPORT_URL = "https://www.ice.com/report/173"
TARGET_API_PATH = "/marketdata/api/reports/173/results"

OUTPUT_DIR = Path("data/raw/robusta_discovery")

API_RESPONSE_FILE = (
    OUTPUT_DIR / "robusta_api_response.json"
)

DISCOVERED_REPORTS_FILE = (
    OUTPUT_DIR / "discovered_reports.json"
)


# Stores API requests that have been received
# but whose response body has not finished loading yet.
pending_requests = {}

# Used to know when a successful API response
# has been completely captured.
response_captured = asyncio.Event()


async def response_received_handler(event, tab):
    """
    Detect the ICE Report 173 API response.

    We only store the request ID here.
    The response body is retrieved later, after
    LoadingFinished is received.
    """

    response_url = event.response.url

    if TARGET_API_PATH not in response_url:
        return

    print("\n" + "=" * 60)
    print("ICE REPORT 173 API RESPONSE DETECTED")
    print("=" * 60)

    print(f"URL: {response_url}")
    print(f"Status: {event.response.status}")

    # Ignore unsuccessful responses.
    if event.response.status != 200:
        print(
            "Ignoring non-successful API response."
        )
        return

    pending_requests[event.request_id] = response_url


async def loading_finished_handler(event, tab):
    """
    Retrieve the API response body after the network
    request has completely finished.
    """

    request_id = event.request_id

    if request_id not in pending_requests:
        return

    response_url = pending_requests.pop(request_id)

    print("\nResponse finished loading.")
    print("Reading response body...")

    try:
        body, is_base64_encoded = await tab.send(
            cdp.network.get_response_body(
                request_id=request_id
            )
        )

        response_text = body

        if is_base64_encoded:
            response_text = base64.b64decode(
                body
            ).decode(
                "utf-8",
                errors="replace",
            )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        API_RESPONSE_FILE.write_text(
            response_text,
            encoding="utf-8",
        )

        print(
            "API response saved to:"
        )
        print(API_RESPONSE_FILE)

        parse_report_urls(response_text)

        response_captured.set()

    except Exception as exc:
        print(
            "Failed to read API response body:"
        )
        print(exc)


def parse_report_urls(response_text: str):
    """
    Extract CSV download URLs from the ICE Report 173
    API response.

    Only CSV files are included.
    PDF downloads are intentionally ignored.
    """

    try:
        payload = json.loads(response_text)

    except json.JSONDecodeError as exc:
        print(
            f"Invalid JSON response: {exc}"
        )
        return

    reports = (
        payload
        .get("datasets", {})
        .get("reports", {})
        .get("rows", [])
    )

    discovered_reports = []

    for row in reports:

        report_date = row.get(
            "reportDate"
        )

        report_list = row.get(
            "reportList",
            [],
        )

        for report in report_list:

            # We only want downloadable reports.
            if report.get("type") != "download":
                continue

            relative_url = report.get(
                "url"
            )

            if not relative_url:
                continue

            # IMPORTANT:
            # Only keep CSV files.
            #
            # ICE also returns PDF downloads,
            # which we don't need for the ETL.
            if not relative_url.lower().endswith(
                ".csv"
            ):
                continue

            if relative_url.startswith("/"):
                full_url = (
                    f"https://www.ice.com"
                    f"{relative_url}"
                )
            else:
                full_url = relative_url

            file_name = Path(
                relative_url
            ).name

            discovered_reports.append(
                {
                    "report_date": report_date,
                    "url": full_url,
                    "file_name": file_name,
                }
            )

    # Remove duplicate report URLs while
    # preserving the original order.
    unique_reports = []
    seen_urls = set()

    for report in discovered_reports:

        report_url = report["url"]

        if report_url in seen_urls:
            continue

        seen_urls.add(report_url)
        unique_reports.append(report)

    discovered_reports = unique_reports

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    DISCOVERED_REPORTS_FILE.write_text(
        json.dumps(
            discovered_reports,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("REPORT URL DISCOVERY COMPLETE")
    print("=" * 60)

    print(
        f"Reports discovered: "
        f"{len(discovered_reports)}"
    )

    print(
        f"Saved to: "
        f"{DISCOVERED_REPORTS_FILE}"
    )

    if not discovered_reports:
        print(
            "\nWARNING: No CSV reports were discovered."
        )
        return

    print("\nFirst report:")

    print(
        json.dumps(
            discovered_reports[0],
            indent=2,
        )
    )

    print("\nLast report:")

    print(
        json.dumps(
            discovered_reports[-1],
            indent=2,
        )
    )

    # Additional validation.
    csv_count = sum(
        1
        for report in discovered_reports
        if report["url"]
        .lower()
        .endswith(".csv")
    )

    pdf_count = sum(
        1
        for report in discovered_reports
        if report["url"]
        .lower()
        .endswith(".pdf")
    )

    print("\nFile type validation:")

    print(
        f"CSV files: {csv_count}"
    )

    print(
        f"PDF files: {pdf_count}"
    )


async def main():

    print("=" * 60)
    print("ROBUSTA REPORT DISCOVERY")
    print("=" * 60)

    print(
        "\nConnecting to existing Edge..."
    )

    browser = await uc.Browser.create(
        host=CDP_HOST,
        port=CDP_PORT,
    )

    print(
        "Connected to Edge."
    )

    # Get the existing ICE Report 173 tab.
    tab = browser[ICE_REPORT_URL]

    print("\nUsing tab:")
    print(
        f"URL: {tab.target.url}"
    )

    # Enable Chrome DevTools Protocol
    # network events.
    await tab.send(
        cdp.network.enable()
    )

    # Listen for the API response.
    tab.add_handler(
        cdp.network.ResponseReceived,
        response_received_handler,
    )

    # Listen for the response to finish loading.
    tab.add_handler(
        cdp.network.LoadingFinished,
        loading_finished_handler,
    )

    print(
        "\nNetwork listener is active."
    )

    print("\n" + "=" * 60)
    print("MANUAL ICE STEPS")
    print("=" * 60)

    print(
        """
1. In the Edge window:

   - Handle the ICE cookie/disclaimer prompts.
   - Click "I ACCEPT" when required.
   - Complete the CAPTCHA manually.

2. Select:

   - Stock Figures

3. Select your required date range.

   For this case study, use approximately
   one year of historical data.

4. Run/search the report.

5. Wait until this terminal shows:

   "REPORT URL DISCOVERY COMPLETE"

6. Only after that, press ENTER here.
"""
    )

    try:

        # Wait up to 10 minutes for the successful
        # API response.
        await asyncio.wait_for(
            response_captured.wait(),
            timeout=600,
        )

        print(
            "\nResponse successfully captured."
        )

    except asyncio.TimeoutError:

        print(
            "\nTimed out waiting for the "
            "ICE API response."
        )

    await asyncio.to_thread(
        input,
        "\nPress ENTER to exit..."
    )


if __name__ == "__main__":
    asyncio.run(main())