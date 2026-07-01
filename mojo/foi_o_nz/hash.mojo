# Experimental native hashing helpers.
# FNV-1a is non-cryptographic and only used for deterministic buckets/cache keys.

alias FNV1A64_OFFSET: UInt64 = 14695981039346656037
alias FNV1A64_PRIME: UInt64 = 1099511628211

fn fnv1a64_update(current: UInt64, byte_value: UInt8) -> UInt64:
    return (current ^ UInt64(byte_value)) * FNV1A64_PRIME


fn fnv1a64_seed() -> UInt64:
    return FNV1A64_OFFSET


fn bounded_bucket(hash_value: UInt64, bucket_count: Int) -> Int:
    if bucket_count <= 0:
        return 0
    return Int(hash_value % UInt64(bucket_count))
