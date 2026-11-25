from tools.app_launcher import launch_app
from tools.browser import open_url, web_search, fetch_page_text
from tools.file_manager import list_directory, read_text_file, write_text_file, delete_file_safely
from tools.screenshot import take_screenshot, get_clipboard, set_clipboard
from tools.pdf_summarizer import extract_pdf_text
from .time_tools import get_current_time

# Map of tool names to functions for dynamic agent execution
AVAILABLE_TOOLS = {
    "launch_app": launch_app,
    "open_url": open_url,
    "web_search": web_search,
    "fetch_page_text": fetch_page_text,
    
    "list_directory": list_directory,
    "read_text_file": read_text_file,
    "write_text_file": write_text_file,
    "delete_file_safely": delete_file_safely,
    "take_screenshot": take_screenshot,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "extract_pdf_text": extract_pdf_text,
    "get_current_time": get_current_time,
}

# ==========================================
# ASTRA STUDENT INTELLIGENCE
# ==========================================

from tools.student_tools import (
    save_student_profile,
    get_student_profile,
    add_subject,
    list_subjects,
    add_assignment,
    list_assignments,
    complete_assignment,
    upcoming_deadlines
)

AVAILABLE_TOOLS.update({

    "save_student_profile": save_student_profile,

    "get_student_profile": get_student_profile,

    "add_subject": add_subject,

    "list_subjects": list_subjects,

    "add_assignment": add_assignment,

    "list_assignments": list_assignments,

    "complete_assignment": complete_assignment,

    "upcoming_deadlines": upcoming_deadlines

})

# ASTRA EXAM INTELLIGENCE

from tools.exam_tools import (
    add_exam,
    list_exams,
    get_exam_syllabus,
    upcoming_exams
)

AVAILABLE_TOOLS.update({
    "add_exam": add_exam,
    "list_exams": list_exams,
    "get_exam_syllabus": get_exam_syllabus,
    "upcoming_exams": upcoming_exams
})

from student.reminders import check_academic_reminders

AVAILABLE_TOOLS.update({
    "check_academic_reminders": check_academic_reminders
})

# ASTRA SYSTEM INTELLIGENCE

from tools.system_tools import (
    get_system_status,
    get_system_information,
    get_battery_status,
    get_system_uptime,
    analyze_system_performance
)

AVAILABLE_TOOLS.update({
    "get_system_status": get_system_status,
    "get_system_information": get_system_information,
    "get_battery_status": get_battery_status,
    "get_system_uptime": get_system_uptime,
    "analyze_system_performance": analyze_system_performance
})