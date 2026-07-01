# Experimental deterministic clock helpers for Mojo.
# These deliberately avoid calendar libraries while the Mojo ecosystem evolves.

fn is_oia_summer_excluded(month: Int, day: Int) -> Bool:
    if month == 12 and day >= 25:
        return True
    if month == 1 and day <= 15:
        return True
    return False


fn is_weekend(weekday: Int) -> Bool:
    # Convention: Monday=0 ... Sunday=6.
    return weekday == 5 or weekday == 6


fn is_machine_working_day(weekday: Int, month: Int, day: Int) -> Bool:
    if is_weekend(weekday):
        return False
    if is_oia_summer_excluded(month, day):
        return False
    return True
