"""Discord UI timeout policy.

Long-lived game surfaces should not expire while the player is reading or briefly away.
Short destructive/confirmation prompts keep their local short timeout values.
"""

GAME_VIEW_TIMEOUT = 1800.0  # 30 minutes of inactivity
CARE_VIEW_TIMEOUT = 3600.0  # home/pet care is the slowest, most idle-friendly surface
SUBMENU_TIMEOUT = 900.0     # inventory/shop/selection submenus
