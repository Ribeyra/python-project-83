URLS_QUERY = """SELECT
    urls.id AS id,
    urls.name AS name,
    lc.last_check AS last_check,
    lc.status_code AS status_code
FROM urls
LEFT JOIN (
    SELECT
        uc.url_id,
        uc.status_code,
        uc.created_at AS last_check
    FROM
        url_checks uc
    JOIN (
        SELECT
            url_id,
            MAX(id) AS max_id
        FROM
            url_checks
        GROUP BY
            url_id
    ) AS latest_checks
    ON
        uc.id = latest_checks.max_id
) AS lc ON urls.id = lc.url_id
ORDER BY id DESC;
"""
