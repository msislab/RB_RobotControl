"""Utility class for building ICV (Imaginary Conveyor) command strings."""

from loguru import logger


class ICVCommandBuilder:
    """Utility class for building ICV (Imaginary Conveyor) command strings."""
    
    @staticmethod
    def build_icv_set_cmd(
        t_sec: float,
        frame: int,
        x_mm: float,
        y_mm: float,
        z_mm: float,
        rx_deg: float = 0.0,
        ry_deg: float = 0.0,
        rz_deg: float = 0.0,
        mode: int = 0,
    ) -> str:
        """
        Builds the icv_set(...) script string.

        Args:
            t_sec: Time in seconds
            frame: 0=Global, 1=Tool, 2~4=User coordinates
            x_mm, y_mm, z_mm: Position offsets in mm
            rx_deg, ry_deg, rz_deg: Rotation offsets in degrees
            mode: 0=Relative, 1=Absolute (confirm with your manual)

        Returns:
            Formatted command string
        """
        cmd = (
            f"icv_set({int(t_sec)},{int(frame)},{int(x_mm)},{int(y_mm)},{int(z_mm)})"
            # f"{int(rx_deg)},{int(ry_deg)},{int(rz_deg)},{int(mode)})"
        )
        logger.info("icv_set cmd: {}", cmd)
        return cmd

