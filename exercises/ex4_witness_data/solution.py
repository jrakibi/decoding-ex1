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

def get_pub_from_priv(priv: bytes) -> bytes:
    """Derive the secp256k1 compressed public key from a private key."""
    sk = SigningKey.from_string(priv, curve=SECP256k1)
    vk = sk.verifying_key
    compressed_pubkey = vk.to_string("compressed")
    return compressed_pubkey

def get_p2wpkh_witness(priv: bytes, msg: bytes) -> bytes:
    """
    Create witness stack for P2WPKH input with format:
    [num_items][sig_len][signature][pubkey_len][pubkey]
    """
    # Get signature with sighash byte
    signature_with_sighash = sign(priv, msg)
    
    # Get compressed public key
    compressed_public_key = get_pub_from_priv(priv)
    
    # Number of witness items (always 2 for P2WPKH)
    num_witness_items = bytes([2])
    
    # Serialize signature with its length
    sig_len = bytes([len(signature_with_sighash)])
    serialized_sig = sig_len + signature_with_sighash
    
    # Serialize public key with its length
    pk_len = bytes([len(compressed_public_key)])
    serialized_pk = pk_len + compressed_public_key
    
    # Combine all parts
    serialized_witness = num_witness_items + serialized_sig + serialized_pk
    return serialized_witness 