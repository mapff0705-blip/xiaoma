
# 导入第三方库
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
# 导入本应用程序提供的方法
from utils.jobManager import append_event
from utils.tools import TavilySearchResults

@CrewBase
class VloginSightCrew():

	agents_config = 'crews/VloginSightCrew/agents.yaml'
	tasks_config = "crews/VloginSightCrew/tasks.yaml"
	# 构造初始化函数，接受job_id作为参数，用于标识作业
	def __init__(self, job_id, llm, inputData):
		self.job_id = job_id
		self.llm = llm
		self.inputData = inputData

	# 定义task的回调函数，在任务完成后记录输出事件
	def append_event_callback(self,task_output):
		append_event(self.job_id, task_output.raw)

	# 通过@agent装饰器定义一个函数，返回一个Agent实例
	@agent
	def vlog_trend_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['vlog_trend_analyst'],
			verbose=True,
			llm=self.llm,
			tools=[TavilySearchResults(), ScrapeWebsiteTool()],
		)

	@task
	def trend_research_task(self) -> Task:
		return Task(
			config=self.tasks_config['trend_research_task'],
			callback=self.append_event_callback,
		)
	@crew
	def crew(self) -> Crew:
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True
		)

	# 定义启动Crew的函数，接受输入参数inputs
	def kickoff(self):
		if not self.crew():
			append_event(self.job_id, "VloginSightCrew not set up")
			return "VloginSightCrew not set up"
		append_event(self.job_id, "VloginSightCrew's Task Started")
		try:
			results = self.crew().kickoff(inputs=self.inputData)
			append_event(self.job_id, "VloginSightCrew's Task Complete")

			return results
		except Exception as e:
			append_event(self.job_id, f"An error occurred: {e}")
			return str(e)

