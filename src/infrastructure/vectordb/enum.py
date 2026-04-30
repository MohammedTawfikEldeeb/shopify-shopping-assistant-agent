from enum import Enum

class VectorDBEnums(Enum):
    Qdrant = "QDRANT"
    PGVector = "PGVECTOR"

class DistanceMetric(Enum):
    COSINE = "cosine"
    DOT_PRODUCT = "dot"

class PgVectorTableSchemeEnums(Enum):
    ID = 'id'
    TEXT = 'text'
    VECTOR = 'vector'
    CHUNK_ID = 'chunk_id'
    METADATA = 'metadata'
    _PREFIX = 'pgvector'

class PgVectorDistanceMethodEnums(Enum):
    COSINE = "vector_cosine_ops"
    DOT = "vector_l2_ops"

class PgVectorIndexTypeEnums(Enum):
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"




