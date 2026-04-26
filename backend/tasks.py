from crewai import Task
from agents import research_agent, hospital_agent, doctor_agent, scheduler_agent

research_task = Task(
    description=(
        "Research the disease/symptom input: {topic}. "
        "Only if user says 'sugar', interpret it as diabetes mellitus and proceed accordingly. "
        "For any other topic, do not add diabetes unless directly relevant. "
        "Use medical web search tools to find symptoms, treatments, and doctor specialization. "
        "Prefer practical, patient-friendly guidance over textbook wording."
    ),
    expected_output=(
        "1. Description\n"
        "2. Symptoms\n"
        "3. Treatments\n"
        "4. Specialist"
    ),
    agent=research_agent,
)

hospital_task = Task(
    description=(
        "You MUST use the hospital_search tool to find hospitals in {location}.\n"
        "DO NOT make up hospital names. Call tool with the location string exactly as given first.\n"
        "Names must be from the same city/area as the provided location.\n"
        "Return up to 5 real hospital names, one per line."
    ),
    expected_output="List of real hospital names found in {location}.",
    agent=hospital_agent,
)

doctor_task = Task(
    description=(
        "You MUST use the doctor_search tool to find doctors and clinics in {location}.\n"
        "DO NOT make up names. Call tool with the location string exactly as given first.\n"
        "Names must be from the same city/area as the provided location.\n"
        "Return up to 5 real doctor/clinic names, one per line."
    ),
    expected_output="List of real doctor and clinic names found in {location}.",
    agent=doctor_agent,
)

schedule_task = Task(
    description=(
        "Create healthcare plan for {topic} using outputs from research, hospital, and doctor tasks. "
        "Keep the response concise (target under 220 words). "
        "Avoid generic boilerplate; provide actionable next steps relevant to the condition. "
        "Your response MUST include these sections:\n"
        "1) Condition Summary\n"
        "2) Symptoms\n"
        "3) Treatment Guidance\n"
        "4) Recommended Specialist\n"
        "5) Hospital Names (copy exact names from hospital task output)\n"
        "6) Doctor/Clinic Names (copy exact names from doctor task output).\n"
        "Use short bullet points only. "
        "List at most 5 hospital names and at most 5 doctor/clinic names. "
        "If fewer names are found, include all available real names and clearly say 'Limited data found'. "
        "Do not include facilities or doctors outside the provided location."
    ),
    expected_output="A concise structured healthcare plan with explicit hospital and doctor names, under 220 words.",
    agent=scheduler_agent,
    context=[research_task, hospital_task, doctor_task],
)