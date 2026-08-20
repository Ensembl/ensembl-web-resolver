from app.api.models.resolver import StableIdResolverContent
from app.core.config import ENSEMBL_URL


def build_stable_id_resolver_content(metadata_results) -> list[StableIdResolverContent]:
    results: list[StableIdResolverContent] = []

    for genome_id in metadata_results:
        metadata = metadata_results[genome_id]

        if not metadata:
            continue

        content = StableIdResolverContent(
            feature_explorer_url=build_feature_explorer_url(
                genome_id,
                metadata["unversioned_stable_id"],
                metadata.get("stable_id_type", "gene"),
                metadata.get("parent_transcript_id"),
            ),
            genome_browser_url=build_genome_browser_url(
                genome_id,
                metadata["unversioned_stable_id"],
                metadata.get("stable_id_type", "gene"),
                metadata.get("parent_transcript_id"),
            ),
            redirect_url=build_redirect_url(
                genome_id,
                metadata["unversioned_stable_id"],
                metadata.get("stable_id_type", "gene"),
                metadata.get("parent_transcript_id"),
            ),
            release_type=metadata.get("release", {}).get("type", ""),
            release_name=metadata.get("release", {}).get("name", ""),
            **metadata,
        )
        results.append(content)

    return results


def build_redirect_url(
    genome_id: str,
    stable_id: str,
    stable_id_type: str = "gene",
    parent_transcript_id: str | None = None,
) -> str:
    if stable_id_type == "protein":
        return build_feature_explorer_url(
            genome_id, stable_id, stable_id_type, parent_transcript_id
        )
    return build_genome_browser_url(
        genome_id, stable_id, stable_id_type, parent_transcript_id
    )


def build_feature_explorer_url(
    genome_id: str,
    stable_id: str,
    stable_id_type: str = "gene",
    parent_transcript_id: str | None = None,
) -> str:
    if stable_id_type == "protein":
        if not parent_transcript_id:
            raise ValueError("Protein stable IDs require a parent transcript ID")
        return (
            f"{ENSEMBL_URL}/feature-explorer/{genome_id}"
            f"/transcript:{parent_transcript_id}?view=protein"
        )
    return f"{ENSEMBL_URL}/feature-explorer/{genome_id}/{stable_id_type}:{stable_id}"


def build_genome_browser_url(
    genome_id: str,
    stable_id: str,
    stable_id_type: str = "gene",
    parent_transcript_id: str | None = None,
) -> str:
    if stable_id_type == "protein":
        if not parent_transcript_id:
            raise ValueError("Protein stable IDs require a parent transcript ID")
        return (
            f"{ENSEMBL_URL}/genome-browser/{genome_id}"
            f"?focus=transcript:{parent_transcript_id}"
        )
    return (
        f"{ENSEMBL_URL}/genome-browser/{genome_id}"
        f"?focus={stable_id_type}:{stable_id}"
    )


def is_json_request(request) -> bool:
    return "application/json" in request.headers.get("accept", "")
