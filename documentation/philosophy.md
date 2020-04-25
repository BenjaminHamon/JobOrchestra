# Philosophy

The project design goal is to build a base toolkit for distributing and running jobs.

The original motivation is the need for a simple and customizable build service, which expanded to the more generic use of running jobs.

The term job refers to any automated action or set of actions that would be performed by a computer. Examples are building an application, running tests, releasing a product, deploying infrastructure configuration, manipulating data sets, performing maintenance, etc.

Job Orchestra is a tool in a global process of automation for tasks that are long, resource intensive, error prone, in need of standardization or versioning. It provides a way to move these tasks from one's computer to the network thus offering more resources and capabilities. It can be used for automatic processes, such as in the context continuous integration and delivery, as well as to give individuals the ability to delegate their local jobs to a worker pool.


## Quality attributes

The project architecture and implementation try to adhere to the following quality attributes:

* Reliability
	* The applications have few bugs and few edge cases.
	* The applications are resilient to failure from other components.

* Maintainability
	* The project has a single primary function and features are selected toward that goal.
	* Related features which do not pertain to the core functions are left to other software which will do a better job of it.
	* The implementation is small and explicit.

* Customizability
	* The implementation is made to be modular and extensible, individual parts and components can be added, modified or removed easily.
	* The implementation does not try to guess the user logic or handle every case. Business logic will be implemented by the user as necessary.
