import pandas as pd
from utils.text import normalize_text
from utils.url import canonicalize_url
from utils.fingerprint import source_priority, _smart_fingerprint
from engine.geo import infer_country_label

def normalize_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizza e deduplica le offerte di lavoro.
    Preferisce job_url_direct su job_url.
    """
    if df.empty:
        return df

    work = df.copy()
    
    if hasattr(work, 'columns'):
        work.columns = [normalize_text(column).lower() for column in work.columns]

    if "job_url_direct" in work.columns:
        work["job_url"] = work.apply(
            lambda row: (normalize_text(row.get("job_url_direct", ""))
                        or normalize_text(row.get("job_url", ""))),
            axis=1,
        )
    elif "job_url" not in work.columns:
        if "url" in work.columns:
            work["job_url"] = work["url"]
        else:
            work["job_url"] = ""

    for column in [
        "title", "company", "location", "description", "site",
        "source_type", "search_country", "date_posted", "job_url",
    ]:
        if column not in work.columns:
            work[column] = ""

    work["title"] = work["title"].apply(normalize_text)
    work["company"] = work["company"].apply(normalize_text)
    work["location"] = work["location"].apply(normalize_text)
    work["description"] = work["description"].apply(normalize_text)
    work["site"] = work["site"].apply(normalize_text)
    work["source_type"] = work["source_type"].apply(normalize_text)
    work["search_country"] = [
        infer_country_label(loc, label)
        for loc, label in zip(work["location"], work["search_country"])
    ]
    work["official_url"] = work["job_url"].apply(canonicalize_url)
    work["job_url"] = work["job_url"].apply(canonicalize_url)
    work["source_priority"] = [
        source_priority(source_type, site)
        for source_type, site in zip(work["source_type"], work["site"])
    ]

    work["job_fingerprint"] = work.apply(
        lambda row: _smart_fingerprint(row.to_dict(), work), axis=1
    )
    work = work.sort_values(["job_fingerprint", "source_priority"], ascending=[True, False])
    work = work.drop_duplicates(subset=["job_fingerprint"], keep="first")

    work = work.sort_values(["source_priority"], ascending=[False])
    non_empty_url = work["job_url"].str.strip() != ""
    deduped_url = work[non_empty_url].drop_duplicates(subset=["job_url"], keep="first")
    work = pd.concat([deduped_url, work[~non_empty_url]], ignore_index=True)

    return work.reset_index(drop=True)
