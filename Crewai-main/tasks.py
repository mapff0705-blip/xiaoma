
import os
from crewai.flow.flow import Flow, listen, start
from VloginSightCrew import VloginSightCrew
from VlogCreationCrew import VlogCreationCrew
from celery import Celery
from utils.jobManager import append_event, get_job_by_id, update_job_by_id
from utils.myLLM import my_llm



# 创建 Celery 实例
app = Celery('my_app', broker='redis://localhost:6379/3')
LLM_TYPE = "qwen"

# 定义flow
class workFlow(Flow):
    # 构造初始化函数，接受job_id作为参数，用于标识作业
    def __init__(self, job_id, llm, inputData):
        super().__init__()
        self.job_id = job_id
        self.llm = llm
        self.inputData = inputData
        self.crew_result=None

    @start()
    def marketAnalystCrew(self):
        result = VloginSightCrew(self.job_id, self.llm, self.inputData).kickoff()
        self.crew_result=result
        return result

    @listen(marketAnalystCrew)
    def contentCreatorCrew(self):
        result = VlogCreationCrew(self.job_id, self.llm, self.inputData,self.crew_result).kickoff()
        return result


# 定义任务
@app.task
def kickoff_flow(job_id, inputData):
    print(f"Flow for job {job_id} is starting")
    results = None
    try:

        append_event(job_id, "Flow Started")
        results = workFlow(job_id, my_llm(LLM_TYPE), inputData).kickoff()
        print(f"Crew for job {job_id} is complete", results)


    except Exception as e:
        print(f"Error in kickoff_flow for job {job_id}: {e}")
        append_event(job_id, f"An error occurred: {e}")
        update_job_by_id(job_id, "ERROR", "Error", ["Flow Start Error"])

    update_job_by_id(job_id, "COMPLETE", str(results), ["Flow complete"])

# celery -A tasks worker --loglevel=info --pool=solo