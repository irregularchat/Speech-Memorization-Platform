# CONTRIBUTING.md

## Collaboration Guidelines

Welcome to the project! We encourage everyone, regardless of skill level, to contribute. Follow these guidelines to help maintain a smooth workflow and ensure a collaborative, productive environment.



### 1. **Setting Up SSH for GitHub Access**

To contribute to the project by pushing code or creating pull requests, it is highly recommended to use **SSH** to securely communicate with GitHub. This will prevent you from entering your username and password every time you push code.

#### Steps to Set Up SSH with GitHub:
1. **Generate an SSH Key**:
   Follow the guide on [SSH Keys](https://irregularpedia.org/index.php/SSH_Keys) to create a new **ED25519 SSH key** on your local machine.

   Example command to generate an ED25519 key:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

   For advanced users, you can generate a key with a passphrase and custom filename:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/your_custom_key -N "your_passphrase"
   ```

2. **Add Your SSH Key to GitHub**:
   After generating your key, follow [GitHub's documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) or the [Irregularpedia guide](https://irregularpedia.org/index.php/SSH_Keys) to add your public key to your GitHub account.

3. **Clone the Repository Using SSH**:
   Now that your SSH key is set up, clone the repository using the SSH URL:
   ```bash
   git clone git@github.com:irregularchat/Speech-Memorization-Platform.git
   ```



### 2. **Forking the Repository and Creating Pull Requests**

Since you'll be contributing code to the project, you will typically fork the repository to make changes in your own copy before submitting them to the main project.

#### Steps for Forking and Creating a Pull Request:
1. **Fork the Repository**:
   Navigate to the [Speech-Memorization-Platform GitHub repository](https://github.com/irregularchat/Speech-Memorization-Platform) and click the "Fork" button in the upper-right corner of the page. This will create a copy of the repository under your own GitHub account.

2. **Clone Your Fork**:
   Clone your forked repository using SSH:
   ```bash
   git clone git@github.com:<your-username>/Speech-Memorization-Platform.git
   ```

3. **Set the Original Repository as Upstream**:
   After cloning, add the original repository as the upstream source to stay up to date with changes in the main project:
   ```bash
   cd Speech-Memorization-Platform
   git remote add upstream git@github.com:irregularchat/Speech-Memorization-Platform.git
   ```

4. **Create a New Branch**:
   Create a new branch for the feature or bug fix you will be working on:
   ```bash
   git checkout -b feature/<short-description>
   ```

5. **Make Changes and Commit**:
   Work on the files, save your changes, test them locally, and then commit:
   ```bash
   git add .
   git commit -m "Add feature X to handle Y"
   ```

6. **Push Your Branch to Your Fork**:
   Push your changes to your forked repository:
   ```bash
   git push origin feature/<short-description>
   ```

7. **Create a Pull Request (PR)**:
   - Go to your forked repository on GitHub.
   - Click the "Compare & pull request" button next to your newly pushed branch.
   - Follow the instructions to create the PR, providing a clear title and description. Ensure your PR references the issue it addresses (e.g., "Fixes #123").



### 3. **Branch Naming Conventions**
   To avoid confusion and keep the repository organized, please follow these branch naming conventions:
   - **Feature branches:** `feature/<short-description>` (e.g., `feature/user-auth`)
   - **Bugfix branches:** `bugfix/<issue-number>` (e.g., `bugfix/123-fix-crash`)
   - **Hotfix branches:** `hotfix/<issue-number>` (e.g., `hotfix/urgent-deploy`)
   - **Documentation updates:** `docs/<short-description>` (e.g., `docs/api-endpoints`)

   Use descriptive names so everyone can easily identify what a branch is for.



### 4. **Working on Files and Making Changes**

   When you're ready to start working on an issue or a feature:
   1. **Check out the main branch** to make sure you have the latest version:
      ```bash
      git checkout main
      git pull origin main
      ```
   2. **Create a new branch** for your work:
      ```bash
      git checkout -b feature/<short-description>
      ```
   3. **Work on the files** in your preferred code editor. Save your changes regularly.
   4. **Test your changes locally** to ensure they work:
      - If you're working on the frontend or backend, run the app locally and ensure it behaves as expected.
      - If you're working on scripts or utilities, run them to verify they produce the correct results.

   5. **Commit your changes**:
      After you're confident that your changes work, save your progress in Git:
      ```bash
      git add .
      git commit -m "Add feature X to handle Y"
      ```
      Make sure your commit messages are **descriptive** so others can understand what the changes are for. Use the imperative mood (e.g., "Add feature X" instead of "Added feature X").



### 5. **Syncing (Pulling and Pushing) Changes**
   
   To avoid conflicts and ensure your changes are always up to date, you should **sync** your branch frequently:
   
   1. **Pull the latest changes from the main branch** to your branch:
      ```bash
      git pull origin main
      ```
      Resolve any merge conflicts if necessary.

   2. Once you've pulled the latest changes, **push your branch** to GitHub:
      ```bash
      git push origin feature/<your-branch-name>
      ```



### 6. **Commit Message Guidelines**
   Good commit messages are crucial for understanding changes to the codebase:
   - **Format:** Use the imperative mood and present tense (e.g., "Add login functionality").
   - **Structure:**
     - **Title:** Short and descriptive (max 50 characters).
     - **Body (optional):** Provide more detail if needed, focusing on what and why rather than how.
   - Example:
     ```
     Add user authentication flow

     Added login and signup pages. Integrated with backend API for token-based authentication.
     ```



### 7. **Use Issue Tracker**
   - Every task should have a corresponding issue in the tracker. This helps keep things organized and allows for discussion before work begins.
   - **Create an issue** for bugs, enhancements, or questions. Clearly describe the problem, goal, or question.
   - **Link issues to pull requests** to show what you’re addressing.



### 8. **Assign Tasks and Collaborate**
   - **Assign yourself to tasks** when you start working on an issue.
   - **Collaborate actively** with other contributors, especially if you are unsure about an approach. Don’t hesitate to ask questions or request feedback.



### 9. **Code Review and Pull Requests**
   - All code contributions should be made via **pull requests**. 
   - Keep your **pull requests small and focused**. It's easier to review and reduces the chance of merge conflicts.
   - **Pull requests should:**
     - Reference the issue they resolve (e.g., "Fixes #123").
     - Include a clear summary of the changes.
     - Have descriptive titles.
   - At least one team member should **review your code** before merging.



### 10. **Avoiding Merge Conflicts**
   - Regularly **pull from the main branch** to stay up to date and minimize merge conflicts.
   - **Communicate with the team** to avoid working on the same part of the codebase.
   - If a conflict arises, **coordinate with the person working on the conflicting section** to resolve it smoothly.



### 11. **Coding Standards**
   - Follow any existing **style guides** and **best practices** for the language and frameworks in use.
   - Ensure your code is **well-documented**, especially when implementing complex logic.
   - Write **unit tests** for any new features or functions.
   - **Keep code readable**: Use descriptive names for variables and functions, and organize your code logically.



### 12. **Tests and Continuous Integration**
   - Write automated tests for any new functionality or changes you implement.
   - Run tests before submitting a pull request to ensure that your code does not introduce any issues.



## Team Collaboration Roles

### Team Leaders
Add your name below to indicate your involvement and responsibility for certain areas. This helps everyone see who’s leading what section and fosters accountability:

- [ ] **Research Team:**
- [ ] **Documentation Team:**
- [ ] **AI Integration Team:**
- [ ] **Frontend Team:**
  - [ ] **Styling Team:**
  - [ ] **User Experience Team:**
- [ ] **Backend Docker Team:**
- [ ] **Deployment Team:**
- [ ] **Testing Team:**