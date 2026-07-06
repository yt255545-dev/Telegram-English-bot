import db


def _display_name(row):
    if row["username"]:
        return f"@{row['username']}"
    return row["first_name"] or f"User {row['user_id']}"


def build_leaderboard_message(year_month, month_label):
    monthly = db.top_monthly(year_month, limit=10)
    alltime = db.top_alltime(limit=10)

    lines = [f"🏆 <b>{month_label} Leaderboard</b> — English Grammar Quiz\n"]

    lines.append("<b>This Month — Top 10</b>")
    if monthly:
        for i, row in enumerate(monthly, 1):
            lines.append(f"{i}. {_display_name(row)} — {row['score']} correct")
    else:
        lines.append("No answers recorded yet this month.")

    lines.append("\n<b>All-Time — Top 10</b>")
    if alltime:
        for i, row in enumerate(alltime, 1):
            lines.append(f"{i}. {_display_name(row)} — {row['score']} correct")
    else:
        lines.append("No answers recorded yet.")

    lines.append("\nKeep answering daily quizzes to climb the board! 📚")
    return "\n".join(lines)
