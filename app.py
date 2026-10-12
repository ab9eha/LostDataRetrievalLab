
import json
import pandas as pd
import streamlit as st

from recovery_engine import (
    create_test_files,
    simulate_deletion,
    recover_test_files,
    get_status,
    get_logs,
    build_report,
    setup_directories
)

st.set_page_config(
    page_title="Lost Data Retrieval Lab",
    page_icon="🔎",
    layout="wide"
)

setup_directories()

st.title("Lost Data Retrieval Lab")
st.caption(
    "Digital forensics practice | Safe deletion simulation | "
    "File integrity verification"
)

st.info(
    "Safety notice: this application uses disposable sample files "
    "inside its own lab folders. Simulated deletion moves files rather "
    "than permanently erasing them. It does not scan your drives."
)

st.sidebar.header("Recovery Workflow")
st.sidebar.write("1. Create sample evidence")
st.sidebar.write("2. Simulate accidental deletion")
st.sidebar.write("3. Recover copies")
st.sidebar.write("4. Verify file integrity")
st.sidebar.write("5. Export the case report")

st.subheader("Experiment Overview")

status = get_status()
columns = st.columns(3)

columns[0].metric("Original files", status["Original files"])
columns[1].metric("Simulated deleted", status["Simulated deleted"])
columns[2].metric("Recovered copies", status["Recovered copies"])

st.divider()
st.subheader("Run the Safe Experiment")

left, middle, right = st.columns(3)

with left:
    st.markdown("**1. Prepare evidence**")
    st.write("Generate three fictional text files and record their hashes.")

    if st.button("Create sample files", use_container_width=True):
        try:
            created = create_test_files()
            st.success(f"Created {len(created)} sample files.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not create files: {error}")

with middle:
    st.markdown("**2. Simulate deletion**")
    st.write("Move test files to a simulated-deleted folder.")

    if st.button("Simulate deletion", use_container_width=True):
        try:
            moved = simulate_deletion()

            if moved:
                st.success(f"Simulated deletion for {moved} files.")
            else:
                st.warning(
                    "No original test files found. Create sample files first."
                )

            st.rerun()
        except Exception as error:
            st.error(f"Simulation failed: {error}")

with right:
    st.markdown("**3. Recover copies**")
    st.write("Copy simulated-deleted files and compare SHA-256 hashes.")

    if st.button("Recover test files", use_container_width=True):
        try:
            recovered = recover_test_files()

            if recovered:
                passed = sum(
                    item["integrity"] == "PASS" for item in recovered
                )
                st.success(
                    f"Created {len(recovered)} recovery copies; "
                    f"{passed} passed integrity checks."
                )
            else:
                st.warning("No simulated-deleted files were found.")

            st.rerun()
        except Exception as error:
            st.error(f"Recovery failed: {error}")

st.divider()
st.subheader("Recovery Results")

report = build_report()
manifest = report["original_manifest"]
logs = report["recovery_log"]

if manifest:
    st.markdown("**Original evidence manifest**")
    st.dataframe(pd.DataFrame(manifest), use_container_width=True)
else:
    st.write("No evidence manifest yet. Create sample files to begin.")

recovery_rows = [
    log for log in logs
    if log["action"] == "RECOVER COPY"
]

if recovery_rows:
    st.markdown("**Recovery activity**")
    st.dataframe(
        pd.DataFrame(recovery_rows),
        use_container_width=True
    )
else:
    st.write("No recovery attempts recorded yet.")

st.divider()

st.divider()
st.subheader("Recovery Analytics")

analytics = get_status()
total_original = len(manifest)
total_deleted = analytics["Simulated deleted"]
total_recovered = analytics["Recovered copies"]

verified = sum(
    log["message"].endswith("PASS.")
    or "integrity: PASS" in log["message"]
    for log in logs
    if log["action"] == "RECOVER COPY"
)

recovery_rate = (
    min(total_recovered, total_deleted) / total_deleted * 100
    if total_deleted else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Original Evidence", total_original)
col2.metric("Simulated Deleted", total_deleted)
col3.metric("Recovered Copies", total_recovered)
col4.metric("Integrity PASS", verified)

st.progress(
    int(recovery_rate),
    text=f"Simulation recovery-copy rate: {recovery_rate:.1f}%"
)

st.caption(
    "This rate measures copies created by the simulator, not real-world "
    "disk recovery success. Integrity counts are derived from the log."
)

st.subheader("Evidence and Report")

st.write(
    "Export a JSON report containing the experiment type, original "
    "manifest, file counts, timestamps, and recorded actions."
)

st.download_button(
    label="Download case report (JSON)",
    data=json.dumps(build_report(), indent=2),
    file_name="lost_data_retrieval_report.json",
    mime="application/json",
    use_container_width=True
)

if logs:
    st.markdown("**Full activity log**")
    st.dataframe(pd.DataFrame(logs), use_container_width=True)

st.divider()
st.subheader("Real Recovery Tools — Separate Experiment")

st.markdown(
    """
    The simulation above is not a real disk-recovery test.

    For a separate experiment with disposable test data:

    - **Recuva:** beginner-friendly deleted-file recovery on Windows.
    - **TestDisk:** open-source recovery utility with file-system-specific
      undelete capabilities.
    - **PhotoRec:** content-based file recovery; original filenames and
      directory structures may not be preserved.

    Use a dedicated test device or isolated test volume. Stop writing to
    the affected storage after deletion, and save recovered data to a
    different device. Never test on your system drive or important files.
    """
)

st.caption(
    "Educational prototype. A matching SHA-256 hash verifies the recovered "
    "copy against the saved manifest; it does not prove that real-world "
    "deleted data was recovered."
)
