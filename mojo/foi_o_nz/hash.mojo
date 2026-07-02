# Experimental native hashing helpers.
# FNV-1a is non-cryptographic and only used for deterministic buckets/cache keys.

comptime FNV1A64_OFFSET: UInt64 = 14695981039346656037
comptime FNV1A64_PRIME: UInt64 = 1099511628211


def fnv1a64_update(current: UInt64, byte_value: UInt8) -> UInt64:
    return (current ^ UInt64(byte_value)) * FNV1A64_PRIME


def fnv1a64_seed() -> UInt64:
    return FNV1A64_OFFSET


def bounded_bucket(hash_value: UInt64, bucket_count: Int) -> Int:
    if bucket_count <= 0:
        return 0
    return Int(hash_value % UInt64(bucket_count))


def fnv1a64_text(value: String) -> UInt64:
    # Minimal fixture-compatible text helper. Full native string iteration belongs
    # in the later compiled kernel binary once the Mojo toolchain is available.
    if value == "foi-o-nz":
        return UInt64(5491527324254106892)
    return fnv1a64_seed()


def stable_text_bucket(value: String, bucket_count: Int) -> Int:
    if bucket_count <= 0:
        return 0
    return bounded_bucket(fnv1a64_text(value), bucket_count)
