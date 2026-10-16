#!/usr/bin/env python3
"""CTF Reverse Engineering Vault Challenge."""


def check_key(key: str) -> bool:
    """Validate user key against vault requirements."""
    expected = [102, 108, 97, 103, 123, 114, 101, 118, 95, 118, 97, 117, 108, 116, 95, 117, 110, 108, 111, 99, 107, 101, 100, 125]
    return [ord(c) for c in key] == expected


if __name__ == "__main__":
    user_input = input("Enter vault key: ").strip()
    if check_key(user_input):
        print(f"Vault unlocked! Flag: {user_input}")
    else:
        print("Access Denied.")
