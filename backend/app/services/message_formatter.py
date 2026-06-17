"""
MessageFormatter
=================
Turns an EOD report payload (from EODReportService.compute) into a WhatsApp
message. Two renderers:

  render_text(payload)            -> pretty multi-line message string.
        Used for: the Admin "Test Send" button, free-form sends inside the
        24h customer-service window, Green API group posts, and logging.

  render_template_params(payload) -> ordered list of single-line strings.
        Used for: Meta Cloud API *template* messages (the only compliant way to
        push an UNSOLICITED scheduled message). Each value is newline-free and
        space-collapsed because Meta rejects template variables containing
        newlines, tabs, or 4+ consecutive spaces.

If you change render_template_params, you must resubmit the WhatsApp template
for approval. The expected approved template body is documented at the bottom
of this file (TEMPLATE_BODY_REFERENCE).
"""

from datetime import date as date_cls

CURRENCY = "₹"  # ₹


def _fmt_money(value) -> str:
    """1234567.5 -> '12,34,567.50' (Indian grouping) prefixed with ₹."""
    n = float(value or 0)
    sign = "-" if n < 0 else ""
    n = abs(n)
    whole = int(n)
    paise = int(round((n - whole) * 100))
    s = str(whole)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        s = ",".join(groups) + "," + last3
    return f"{sign}{CURRENCY}{s}.{paise:02d}"


def _fmt_date(iso: str) -> str:
    d = date_cls.fromisoformat(iso)
    return d.strftime("%d %b %Y")


def _collapse(text: str) -> str:
    """Make a string safe for a Meta template variable: no newlines/tabs and no
    runs of 4+ spaces."""
    text = " ".join(str(text).split())
    return text


class MessageFormatter:
    @staticmethod
    def render_text(payload: dict) -> str:
        s = payload["sales"]
        p = payload["purchases"]
        inv = payload["inventory"]
        act = payload["stock_activity"]
        snap = payload["snapshot"]

        top = s.get("top_products") or []
        if top:
            top_str = ", ".join(f"{t['name']} ({t['quantity']})" for t in top[:3])
        else:
            top_str = "—"  # —

        net = snap["net_stock_change"]
        net_arrow = "▲ +" if net > 0 else ("▼ " if net < 0 else "")

        lines = [
            "\U0001f4ca *VVV STOCK — EOD Report*",
            f"\U0001f5d3️ {_fmt_date(payload['report_date'])}",
            "",
            "*— SALES —*",
            f"\U0001f4b0 Total Sales:   {_fmt_money(s['total_amount'])}  ({s['transaction_count']} txns)",
            f"\U0001f4e6 Qty Sold:      {s['total_quantity']} units",
            f"\U0001f3c6 Top: {top_str}",
            "",
            "*— PURCHASES —*",
            f"\U0001f6d2 Total Purchases: {_fmt_money(p['total_amount'])}  ({p['transaction_count']} txns)",
            f"\U0001f4e5 Qty Purchased:   {p['total_quantity']} units",
            "",
            "*— INVENTORY —*",
            f"\U0001f9fe Products:       {inv['total_products']}",
            f"\U0001f4e6 Stock on hand:  {inv['total_stock_on_hand']} units",
            f"⚠️ Low stock:      {inv['low_stock_products']}",
            f"❌ Out of stock:   {inv['out_of_stock_products']}",
            f"\U0001f501 Reorder needed: {inv['reorder_required_products']}",
            "",
            "*— STOCK ACTIVITY —*",
            f"➕ Stock-in txns:  {act['stock_in_transactions']}",
            f"\U0001f527 Adjustments:    {act['stock_adjustment_transactions']}",
            "",
            "*— SNAPSHOT —*",
            f"Opening value: {_fmt_money(snap['opening_stock_value'])}",
            f"Closing value: {_fmt_money(snap['closing_stock_value'])}",
            f"Net change:    {net_arrow}{_fmt_money(abs(net))}",
        ]
        return "\n".join(lines)

    @staticmethod
    def render_template_params(payload: dict) -> list[str]:
        """Ordered, newline-free params for the approved Meta template.
        Order MUST match TEMPLATE_BODY_REFERENCE ({{1}}..{{12}})."""
        s = payload["sales"]
        p = payload["purchases"]
        inv = payload["inventory"]
        act = payload["stock_activity"]
        snap = payload["snapshot"]

        top = s.get("top_products") or []
        top_str = (
            ", ".join(f"{t['name']} ({t['quantity']})" for t in top[:3])
            if top
            else "None"
        )

        return [
            _collapse(_fmt_date(payload["report_date"])),                         # {{1}}
            _collapse(f"{_fmt_money(s['total_amount'])} ({s['transaction_count']} txns)"),  # {{2}}
            _collapse(f"{s['total_quantity']} units"),                            # {{3}}
            _collapse(top_str),                                                   # {{4}}
            _collapse(f"{_fmt_money(p['total_amount'])} ({p['transaction_count']} txns)"),  # {{5}}
            _collapse(f"{p['total_quantity']} units"),                            # {{6}}
            _collapse(
                f"{inv['total_products']} products, {inv['total_stock_on_hand']} units"
            ),                                                                    # {{7}}
            _collapse(
                f"Low {inv['low_stock_products']}, Out {inv['out_of_stock_products']}, "
                f"Reorder {inv['reorder_required_products']}"
            ),                                                                    # {{8}}
            _collapse(
                f"In {act['stock_in_transactions']}, Adj {act['stock_adjustment_transactions']}"
            ),                                                                    # {{9}}
            _collapse(_fmt_money(snap["opening_stock_value"])),                   # {{10}}
            _collapse(_fmt_money(snap["closing_stock_value"])),                   # {{11}}
            _collapse(_fmt_money(snap["net_stock_change"])),                      # {{12}}
        ]


# ── Reference: the WhatsApp template body you submit to Meta for approval ──────
# Category: UTILITY    Language: en
# Name: e.g. "vvv_eod_report"  (put this in settings 'eod.template_name')
#
# Body:
#   📊 VVV STOCK — EOD Report
#   🗓️ {{1}}
#
#   SALES
#   Total: {{2}}
#   Qty Sold: {{3}}
#   Top: {{4}}
#
#   PURCHASES
#   Total: {{5}}
#   Qty: {{6}}
#
#   INVENTORY
#   {{7}}
#   {{8}}
#
#   STOCK ACTIVITY: {{9}}
#
#   SNAPSHOT
#   Opening: {{10}}
#   Closing: {{11}}
#   Net change: {{12}}
TEMPLATE_BODY_REFERENCE = "See module docstring / comment above (12 variables)."
