# MzansiBuilds

## Project profiling

To begin the MzansiBuilds project, I first focused on understanding the requirements and the problem the platform is trying to solve. The idea behind the platform is to allow developers to build projects publicly while sharing their progress and collaborating with other developers. Based on the requirements provided in the challenge, the main features of the system include user account creation and management, creating and updating projects, viewing what other developers are working on, interacting through comments or collaboration requests, tracking project milestones, and displaying completed projects on a celebration wall.

After reviewing the requirements, I broke the system down into smaller functional areas so that it would be easier to plan and implement. These areas included authentication for user accounts, project management for creating and updating projects, a developer feed where users can see projects from other developers, milestone tracking to record progress, and a section that highlights completed projects.

Before starting with the implementation, I created diagrams to help visualise the system structure and how the different parts of the application interact with each other. I designed a system architecture diagram to show how the user interface communicates with the backend and database. I also created an entity relationship diagram to outline the database structure and the relationships between users, projects, milestones, and comments. In addition, I mapped out the user flow to understand the typical journey a developer would take on the platform from registering an account to completing a project.

Creating these diagrams helped me organise the project and think through the design before writing any code. This made it easier to understand how the different components of the system connect and ensured that the development process would follow a clear and structured approach.


## System architecture
![System Architecture](docs/architecture.drawio.png)

## Database Design
![Database ER Diagram](docs/ERD.drawio.png)

## User Flow
![User Flow](docs/user-flow_diagram.drawio.png)

## Component Level
![Component Level](docs/component_level.drawio.png)