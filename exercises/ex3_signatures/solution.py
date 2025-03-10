import hashlib
from ecdsa import SigningKey, SECP256k1, util

def int_to_little_endian(value: int, length: int) -> bytes:
    """Convert an integer to little-endian bytes"""
    return value.to_bytes(length, 'little')

def dsha256(data: bytes) -> bytes:
    """Double SHA256 hash"""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def sign(private_key: bytes, commitment: bytes) -> bytes:
    """
    Sign a commitment hash with a private key.
    Returns DER-encoded signature with SIGHASH_ALL byte appended.
    
    Args:
        private_key: 32-byte private key
        commitment: 32-byte commitment hash to sign
        
    Returns:
        DER-encoded signature + SIGHASH_ALL byte
    """
    # Create signing key from private key bytes
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    
    while True:
        # Create deterministic signature (RFC 6979)
        signature_der = sk.sign_digest_deterministic(
            commitment,
            hashfunc=hashlib.sha256,
            sigencode=util.sigencode_der
        )
        
        # Decode signature to get r and s values
        r, s = util.sigdecode_der(signature_der, SECP256k1.order)

        # Check if s is high (BIP62)
        if s > SECP256k1.order // 2:
            s = SECP256k1.order - s  # Convert to low-s
            # Re-encode with low-s
            signature_der = util.sigencode_der(r, s, SECP256k1.order)

        # Add SIGHASH_ALL byte
        signature_with_sighash = signature_der + b'\x01'
        
        # Only exit if we have low-s
        if s <= SECP256k1.order // 2:
            break
            
    return signature_with_sighash 