from crewai import Crew, Process
from agents import research_agent, hospital_agent, scheduler_agent, doctor_agent
from tasks import research_task, hospital_task, schedule_task, doctor_task


crew = Crew(
    agents=[
        research_agent,
        hospital_agent,
        doctor_agent,
        scheduler_agent
        
    ],
    tasks=[
        research_task,
        hospital_task,
        doctor_task,
        schedule_task   
    ],
    process=Process.sequential,
    verbose=False,
    
)