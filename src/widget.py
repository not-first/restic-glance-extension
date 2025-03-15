def parse_widget_html(data: dict) -> str:
    snapshot = data.get("latest_snapshot", {})
    stats = data.get("stats", {})
    hide_file_count = data.get("hide_file_count", False)

    snapshot_id = snapshot.get("id", "")
    snapshot_time = snapshot.get("readable_time", "")

    method = snapshot.get("method", "")
    method_icon = ""
    if method == "manual":
        method_icon = """
        <svg data-popover-type="text" data-popover-text="Backed up manually" style="height:1em;vertical-align:middle;margin-right:0.5em;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 0 0-11.215 0c-.22.578.254 1.139.872 1.139h9.47Z" />
        </svg>"""
    elif method == "cron":
        method_icon = """
        <svg data-popover-type="text" data-popover-text="Backed up using cron" style="height:1em;vertical-align:middle;margin-right:0.5em;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor">
          <path fill-rule="evenodd" d="M1 8a7 7 0 1 1 14 0A7 7 0 0 1 1 8Zm7.75-4.25a.75.75 0 0 0-1.5 0V8c0 .414.336.75.75.75h3.25a.75.75 0 0 0 0-1.5h-2.5v-3.5Z" clip-rule="evenodd" />
        </svg>"""

    snapshots_count = stats.get("snapshots_count", "")
    total_file_count = stats.get("file_count", "")
    total_size = stats.get("total_size", "")

    other_snaps = data.get("other_snapshots", [])
    margin_bottom_class = "margin-bottom-10" if other_snaps else ""

    # Prepare stats list items based on hide_file_count parameter
    stats_items = [f"<li>{snapshots_count} snapshots</li>"]
    if not hide_file_count:
        stats_items.append(f"<li>{total_file_count} files</li>")
    stats_items.append(f"<li>{total_size}</li>")

    stats_html = "".join(stats_items)

    main_html = f"""
    <div class="{margin_bottom_class}">
      <p style="display:inline-flex;align-items:center;" class="size-h4 color-highlight">
        {method_icon}{snapshot_id} - {snapshot_time}
      </p>
      <ul class="list-horizontal-text color-subdued">
        {stats_html}
      </ul>
    </div>
    """

    if not other_snaps:
        return main_html

    items_html = ""

    for snap in other_snaps:
        sid = snap.get("id", "")
        stime = snap.get("readable_time", "")
        items_html += f"""
        <li>
          <ul class="list-horizontal-text">
            <li>{sid}</li>
            <li class="color-subdue">{stime}</li>
          </ul>
        </li>"""
    return main_html + f"""
      <div style="margin-top:1em; border-top: 1px solid var(--color-separator); padding-top:1em;">
        <ul class="list list-gap-10 ">
          {items_html}
        </ul>
      </div>
    """
