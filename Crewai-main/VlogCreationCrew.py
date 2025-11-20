
# 导入第三方库
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import  ScrapeWebsiteTool

from utils.models import VlogConceptProposal,StoryboardOutline,VlogScript,PublishingOptimizationPlan
from utils.jobManager import append_event
from utils.tools import TavilySearchResults

@CrewBase
class VlogCreationCrew():
	agents_config = 'crews/VlogCreationCrew/agents.yaml'
	tasks_config = 'crews/VlogCreationCrew/tasks.yaml'
	# 构造初始化函数，接受job_id作为参数，用于标识作业
	def __init__(self, job_id, llm, inputData,crew_result=None):
		self.job_id = job_id
		self.llm = llm
		self.inputData = inputData
		self.crew_result=crew_result

	# 定义task的回调函数，在任务完成后记录输出事件
	def append_event_callback(self,task_output):
		append_event(self.job_id, task_output.raw)



	# 通过@agent装饰器定义一个函数，返回一个Agent实例
	@agent
	def vlog_content_strategist(self) -> Agent:
		return Agent(
			config=self.agents_config['vlog_content_strategist'],
			verbose=True,
			llm=self.llm,
			tools=[TavilySearchResults(), ScrapeWebsiteTool()],
		)
	@agent
	def creative_scriptwriter(self) -> Agent:
		return Agent(
			config=self.agents_config['creative_scriptwriter'],
			verbose=True,
			llm=self.llm
		)



	# 通过@task装饰器定义一个函数，返回一个Task实例
	@task
	def vlog_concept_task(self) -> Task:
		return Task(
			config=self.tasks_config['vlog_concept_task'],
			callback=self.append_event_callback,
			context=[self.crew_result],
			output_json=VlogConceptProposal
		)

	@task
	def story_structure_task(self) -> Task:
		return Task(
			config=self.tasks_config['story_structure_task'],
			callback=self.append_event_callback,
			context=[self.vlog_concept_task()],
			output_json=StoryboardOutline
		)
	@task
	def scriptwriting_task(self) -> Task:
		return Task(
			config=self.tasks_config['scriptwriting_task'],
			callback=self.append_event_callback,
			context=[self.story_structure_task()],
			output_json=VlogScript
		)

	@task
	def publishing_optimization_task(self) -> Task:
		return Task(
			config=self.tasks_config['publishing_optimization_task'],
			callback=self.append_event_callback,
			context=[self.scriptwriting_task()],
			output_json=PublishingOptimizationPlan
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
			append_event(self.job_id, "VlogCreationCrew not set up")
			return "VlogCreationCrew not set up"
		append_event(self.job_id, "VlogCreationCrew's Task Started")
		try:
			results = self.crew().kickoff(inputs=self.inputData)
			append_event(self.job_id, "VlogCreationCrew's Task Complete")

			return results
		except Exception as e:
			append_event(self.job_id, f"An error occurred: {e}")
			return str(e)

