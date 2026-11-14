"""Run a small live IRSA SIA2 metadata query."""

from __future__ import annotations

import astropy.units as u

from astronomy_backend.irsa import IRSAClient, create_query


def main() -> None:
    query = create_query(
        ra=269.45208 * u.deg,
        dec=4.69339 * u.deg,
        radius=6 * u.arcmin,
        collection="spherex_dr1",
    )
    observations = IRSAClient().search(query, max_records=10)
    print(f"Retrieved {len(observations)} observation(s).")
    for observation in observations:
        print(
            observation.observation_id,
            observation.access_url,
            observation.image_format,
        )


if __name__ == "__main__":
    main()
