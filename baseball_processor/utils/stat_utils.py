class StatUtils:
    """Shared stat conversions and small helpers."""

    @staticmethod
    def ip_to_outs(ip):
        """Convert baseball IP string/number (e.g., '7.2') to outs (e.g., 23)."""
        try:
            s = str(ip)
            if "." in s:
                whole, frac = s.split(".")
                return int(whole) * 3 + int(frac)
            return int(float(s)) * 3
        except Exception:
            return None

    @staticmethod
    def outs_to_baseball_ip(outs):
        """Convert outs (int) back to baseball IP float notation (e.g., 23 -> 7.2)."""
        try:
            outs = int(outs)
            whole = outs // 3
            rem = outs % 3
            return float(f"{whole}.{rem}")
        except Exception:
            return 0.0

# Legacy functions for backwards compatibility
