from app.api.models.resolver import StableIdResolverContent
from app.core.config import ENSEMBL_URL


def build_stable_id_resolver_content(metadata_results) -> list[StableIdResolverContent]:
    results: list[StableIdResolverContent] = []

    for genome_id in metadata_results:
        metadata = metadata_results[genome_id]

        if not metadata:
            continue

        content = StableIdResolverContent(
            entity_viewer_url=build_entity_viewer_url(genome_id, metadata['unversioned_stable_id']),
            genome_browser_url=build_genome_browser_url(genome_id, metadata['unversioned_stable_id']),
            **metadata,
        )
        results.append(content)

    return results


def build_entity_viewer_url(genome_id: str, stable_id: str) -> str:
    return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{stable_id}"


def build_genome_browser_url(genome_id: str, stable_id: str) -> str:
    return f"{ENSEMBL_URL}/genome-browser/{genome_id}?focus=gene:{stable_id}"


def is_json_request(request) -> bool:
    return "application/json" in request.headers.get("accept")
