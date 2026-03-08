import os
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from scanner import scan_folder, get_recent_file
from duplicate_detector import (
    find_duplicates,
    find_duplicate_groups,
    summarize_duplicate_stats,
)
from carbon_calculator import calculate_carbon
from old_file_detector import find_old_files_by_days
from usage_detector import detect_usage
from smart_labels import label_files
from personalization import update_preferences


st.set_page_config(page_title="ZeroByte", page_icon="🌱", layout="wide")

st.markdown("### 🌱 ZeroByte - Digital Carbon Manager")
st.markdown(
)


with st.sidebar:
    st.markdown("### 📁 Scan Settings")
    folder = st.text_input("Folder to analyze", value=st.session_state.get("folder", ""))

    st.markdown("**Old file threshold**")
    old_days = st.radio("Not modified for at least:", [90, 180, 365], index=1, horizontal=True)

    st.markdown("**Usage thresholds**")
    unused_days = st.slider(
        "Unused = not accessed for (days)", min_value=60, max_value=365, value=180, step=15
    )
    rarely_days = st.slider(
        "Rarely used = not accessed for (days)", min_value=7, max_value=90, value=30, step=1
    )

    scan_clicked = st.button("🔍 Scan & Analyze")


if scan_clicked:
    if not os.path.exists(folder):
        st.error("Folder path not found")
    else:
        st.session_state["folder"] = folder

        with st.spinner("Scanning files and computing impact..."):
            total_files, total_size = scan_folder(folder)
            size_gb, total_co2 = calculate_carbon(total_size)

            duplicate_groups = find_duplicate_groups(folder)
            dup_total_files, dup_total_size, dup_savings = summarize_duplicate_stats(
                duplicate_groups
            )
            duplicates_flat = find_duplicates(folder)

            old_files = find_old_files_by_days(folder, old_days)

            unused_files, rarely_used_files = detect_usage(
                folder, unused_days=unused_days, rarely_used_days=rarely_days
            )

            labeled_files, label_counts = label_files(folder)

            label_storage = Counter()

            file_types = []
            largest_files = []

            for root, dirs, files in os.walk(folder):
                for file in files:
                    path = os.path.join(root, file)

                    try:
                        ext = os.path.splitext(file)[1] or "no_ext"
                        file_types.append(ext)

                        size = os.path.getsize(path)
                        largest_files.append((file, size, path))
                    except OSError:
                        continue

           
            for item in labeled_files:
                path = item["path"]
                label = item["label"]
                try:
                    size = os.path.getsize(path)
                    label_storage[label] += size
                except OSError:
                    continue

            largest_files.sort(key=lambda x: x[1], reverse=True)
            file_type_counts = Counter(file_types)

           
            unused_size = 0
            for path in unused_files:
                try:
                    unused_size += os.path.getsize(path)
                except OSError:
                    continue

            _, unused_co2 = calculate_carbon(unused_size)
            _, dup_savings_co2 = calculate_carbon(dup_savings)

            potential_reduction_gb = (unused_size + dup_savings) / (1024**3)
            potential_reduction_co2 = unused_co2 + dup_savings_co2

            if total_size > 0:
                unused_pct = (unused_size / total_size) * 100
                dup_pct = (dup_savings / total_size) * 100
            else:
                unused_pct = dup_pct = 0.0

            eco_score = max(0.0, 100.0 - (unused_pct + dup_pct))

            recent_file = get_recent_file(folder)

            st.session_state.update(
                {
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "size_gb": size_gb,
                    "carbon_total": total_co2,
                    "duplicate_groups": duplicate_groups,
                    "duplicate_stats": {
                        "total_files": dup_total_files,
                        "total_size_bytes": dup_total_size,
                        "potential_savings_bytes": dup_savings,
                    },
                    "duplicates_flat": duplicates_flat,
                    "old_files": old_files,
                    "old_days": old_days,
                    "unused_files": unused_files,
                    "rarely_used_files": rarely_used_files,
                    "unused_size_bytes": unused_size,
                    "unused_co2": unused_co2,
                    "duplicate_savings_bytes": dup_savings,
                    "duplicate_savings_co2": dup_savings_co2,
                    "potential_reduction_gb": potential_reduction_gb,
                    "potential_reduction_co2": potential_reduction_co2,
                    "eco_score": eco_score,
                    "file_types": file_type_counts,
                    "largest_files": largest_files[:10],
                    "labeled_files": labeled_files,
                    "label_counts": label_counts,
                    "label_storage_bytes": dict(label_storage),
                    "recent_file": recent_file,
                }
            )


if "total_files" in st.session_state:
    st.markdown("### 📊 Overview Metrics")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Files", st.session_state["total_files"])
    col2.metric("Storage Used", f"{st.session_state['size_gb']:.2f} GB")
    col3.metric(
        "CO₂ Impact", f"{st.session_state['carbon_total']:.3f} kg / year"
    )
    col4.metric(
        "Potential CO₂ Reduction",
        f"{st.session_state['potential_reduction_co2']:.3f} kg / year",
    )

    st.markdown("### 🌍 Eco Score")
    eco_col1, eco_col2 = st.columns([1, 2])
    eco_col1.metric(
        "Eco Score", f"{st.session_state['eco_score']:.0f} / 100"
    )
    eco_col2.markdown(
        "Higher scores mean **less duplicate and unused data** relative to your total storage."
    )


if "file_types" in st.session_state:
    st.markdown("### 📁 File Type Distribution")
    ft_counts = st.session_state["file_types"]
    if ft_counts:
        df_ft = pd.DataFrame(
            {"extension": list(ft_counts.keys()), "count": list(ft_counts.values())}
        ).sort_values("count", ascending=False)
        fig_ft = px.bar(
            df_ft,
            x="extension",
            y="count",
            title="File Types",
            labels={"extension": "Extension", "count": "Files"},
        )
        st.plotly_chart(fig_ft, use_container_width=True)


st.markdown("### 🗑 Duplicate Files")
duplicate_groups = st.session_state.get("duplicate_groups", [])
dup_stats = st.session_state.get("duplicate_stats", {})

if not duplicate_groups:
    st.info("No duplicate file groups detected in the scanned folder.")
else:
    total_groups = len(duplicate_groups)
    total_dup_files = dup_stats.get("total_files", 0)
    potential_savings_bytes = dup_stats.get("potential_savings_bytes", 0)
    potential_savings_gb = potential_savings_bytes / (1024**3)

    c1, c2, c3 = st.columns(3)
    c1.metric("Duplicate Groups", total_groups)
    c2.metric("Files in Groups", total_dup_files)
    c3.metric("Potential Storage Saved", f"{potential_savings_gb:.2f} GB")

    select_all_dup = st.checkbox(
        "Select all duplicate copies (keep one per group)", value=False
    )
    selected_dup: list[str] = []

    for idx, group in enumerate(duplicate_groups, start=1):
        with st.expander(f"Group {idx} – {len(group)} files"):
            if group:
                st.write("Keeping:", group[0])
            for path in group[1:]:
                if select_all_dup:
                    st.checkbox(
                        path,
                        value=True,
                        key=f"dup_{idx}_{path}",
                        disabled=True,
                    )
                    selected_dup.append(path)
                else:
                    checked = st.checkbox(path, key=f"dup_{idx}_{path}")
                    if checked:
                        selected_dup.append(path)

    if st.button("Delete Selected Duplicates"):
        deleted_size = 0
        for file in selected_dup:
            try:
                deleted_size += os.path.getsize(file)
                os.remove(file)
            except OSError:
                continue

        saved_gb = deleted_size / (1024**3)
        _, carbon_saved = calculate_carbon(deleted_size)

        st.success(f"{len(selected_dup)} duplicate files deleted.")
        st.metric("Storage Freed", f"{saved_gb:.2f} GB")
        st.metric("Carbon Saved", f"{carbon_saved:.3f} kg / year")


st.markdown("### ⌛ Old Files")

if "folder" in st.session_state:
    age_days = st.radio(
        "Show files not accessed for at least:",
        [90, 180, 365],
        index={90: 0, 180: 1, 365: 2}.get(
            st.session_state.get("old_days", 180), 1
        ),
        horizontal=True,
        key="old_filter_days",
    )
    old_files = find_old_files_by_days(st.session_state["folder"], age_days)

    st.write(f"{len(old_files)} files not accessed for {age_days}+ days.")

    selected_old: list[str] = []
    with st.expander("View old files"):
        for f in old_files[:200]:
            if st.checkbox(f, key=f"old_{f}"):
                selected_old.append(f)

    if st.button("Delete Selected Old Files"):
        deleted_size = 0
        for file in selected_old:
            try:
                deleted_size += os.path.getsize(file)
                os.remove(file)
            except OSError:
                continue

        saved_gb = deleted_size / (1024**3)
        _, carbon_saved = calculate_carbon(deleted_size)

        st.success(f"{len(selected_old)} old files deleted.")
        st.metric("Storage Freed", f"{saved_gb:.2f} GB")
        st.metric("Carbon Saved", f"{carbon_saved:.3f} kg / year")


st.markdown("### 💤 Unused & Rarely Used Files")

unused_files = st.session_state.get("unused_files", [])
rarely_used_files = st.session_state.get("rarely_used_files", [])

if not unused_files and not rarely_used_files:
    st.info("Scan a folder to see unused and rarely used files.")
else:
    col_u, col_r = st.columns(2)
    col_u.metric("Unused files", len(unused_files))
    col_r.metric("Rarely used files", len(rarely_used_files))

    selected_unused: list[str] = []
    with st.expander("View unused files (safe cleanup candidates)"):
        for f in unused_files[:200]:
            if st.checkbox(f, key=f"unused_{f}"):
                selected_unused.append(f)

    if st.button("Delete Selected Unused Files"):
        deleted_size = 0
        for file in selected_unused:
            try:
                deleted_size += os.path.getsize(file)
                os.remove(file)
            except OSError:
                continue

        saved_gb = deleted_size / (1024**3)
        _, carbon_saved = calculate_carbon(deleted_size)

        st.success(f"{len(selected_unused)} unused files deleted.")
        st.metric("Storage Freed", f"{saved_gb:.2f} GB")
        st.metric("Carbon Saved", f"{carbon_saved:.3f} kg / year")

    with st.expander("View rarely used files"):
        for f in rarely_used_files[:200]:
            st.text(f)


st.markdown("### 🧠 Smart Labels & Personalization")

labeled_files = st.session_state.get("labeled_files", [])
label_counts = st.session_state.get("label_counts", {})
label_storage_bytes = st.session_state.get("label_storage_bytes", {})

if not labeled_files:
    st.info("Run a scan to see smart labels for your files.")
else:
    col_w, col_p, col_t = st.columns(3)
    col_w.metric("Work files", label_counts.get("Work", 0))
    col_p.metric("Personal files", label_counts.get("Personal", 0))
    col_t.metric("Temporary files", label_counts.get("Temporary", 0))

    df_labels = pd.DataFrame(
        {
            "label": list(label_counts.keys()),
            "count": list(label_counts.values()),
        }
    )
    fig_labels = px.pie(
        df_labels,
        names="label",
        values="count",
        title="Label Distribution",
    )
    st.plotly_chart(fig_labels, use_container_width=True)

    if label_storage_bytes:
        df_ls = pd.DataFrame(
            {
                "label": list(label_storage_bytes.keys()),
                "gb": [
                    v / (1024**3) for v in label_storage_bytes.values()
                ],
            }
        )
        fig_ls = px.bar(
            df_ls,
            x="label",
            y="gb",
            title="Storage Usage by Label (GB)",
            labels={"gb": "Storage (GB)", "label": "Label"},
        )
        st.plotly_chart(fig_ls, use_container_width=True)

    st.markdown("#### Adjust labels (teaches the AI)")

    options = ["Work", "Personal", "Temporary", "Unknown"]
    corrections: list[tuple[str, str]] = []

    for item in labeled_files[:50]:
        current = item["label"]
        try:
            idx = options.index(current)
        except ValueError:
            idx = options.index("Unknown")

        new_label = st.selectbox(
            item["name"],
            options=options,
            index=idx,
            key=f"lbl_{item['path']}",
        )

        if new_label != current:
            corrections.append((item["path"], new_label))

    if st.button("Save label corrections"):
        for path, lbl in corrections:
            update_preferences(path, lbl)
        st.success(
            "Preferences saved. Re-run the scan to see updated smart labels."
        )


st.markdown("### Carbon Impact Breakdown")

if "carbon_total" in st.session_state:
    total_co2 = st.session_state["carbon_total"]
    unused_co2 = st.session_state.get("unused_co2", 0.0)
    dup_co2 = st.session_state.get("duplicate_savings_co2", 0.0)
    potential_reduction_co2 = st.session_state.get(
        "potential_reduction_co2", 0.0
    )

    df_ci = pd.DataFrame(
        {
            "category": [
                "Total footprint",
                "Unused data (if removed)",
                "Duplicate data (if removed)",
                "Potential reduction",
            ],
            "kg_co2_per_year": [
                total_co2,
                unused_co2,
                dup_co2,
                potential_reduction_co2,
            ],
        }
    )

    fig_ci = px.bar(
        df_ci,
        x="category",
        y="kg_co2_per_year",
        title="Digital Carbon Impact (kg CO₂ per year)",
        labels={"kg_co2_per_year": "kg CO₂ / year", "category": "Category"},
    )
    st.plotly_chart(fig_ci, use_container_width=True)


st.markdown("### 📦 Largest Files & Recent Activity")

largest = st.session_state.get("largest_files", [])
recent_file = st.session_state.get("recent_file")

col_l, col_r = st.columns(2)

with col_l:
    st.markdown("#### Largest files")
    for file, size, path in largest:
        st.write(f"{file} – {size/(1024**2):.2f} MB")

with col_r:
    st.markdown("#### Most recently accessed file")
    if recent_file:
        st.write(recent_file)
    else:
        st.write("No recent file information available yet.")
