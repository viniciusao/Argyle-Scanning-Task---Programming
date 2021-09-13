# Usage and settings
 1. **Default**:
      <br>
      <br>
      1 - `git clone this_repo` ; `cd this_repo` ; `pip install flit`; `flit install
      <br>
      <br>
      2 - **python run src/spider.py**
      <br>
      <br>

 2. **Docker**:
      <br>
      <br>
      1 - `git clone this_repo` ; `cd this_repo` ; docker build . -t argyle_test:latest
      <br>
      <br>
      2 - **run** modes:
            <br>
            2.1 - *docker run argyle_test:latest*
            <br>
            2.2 - **docker run --rm -it --entrypoint bash argyle_test:latest ; python /opt/argyle_test/src/spider.py ; ls | grep /opt/argyle_test/src/*.json**


# Rationale
- *Architecture suggestion*: **pub/sub**, even though I didn't implement it for the sake of simplicity. 
- *How did you do?* [**Part 1**]  I reversed engineered *Upwork's* login process, and **PerimeterX** AI's antibot system protects them. Eventually, the `src/spider.py` is requested to prove that it's not a robot. I can solve the captchas, but my spider makes pure HTTP requests, so I can't render JavaScript. That means I can't go further with the *"I'm not a robot"* process because, with the ReCaptcha answer key, their server injects in you a script.js (very obscure, I wasn't able to decode it 100%) to validate it and then delivers a cookie, this cookie is the only one you need to browser around *Upwork's* website.
- *How did you do?* [**Part 2**] I've noticed that they ban you based on your **user-agent and IP** and that such cookie is associated with that IP address and user-agent, so I thought about **Proxy rotation + render JS**, and I've found a service that provides that for free (quota of 1k requests). Bypass done.
- *Storage*: That cookie and user-agent are stored in a `sqlite.db` for the sake of simplicity.
- *Spider*: Logins already stored in `sqlite.db` are retrieved and enqueued to execute asynchronously (**async/await httpx, asyncio**) by `src/spider.py`
- *Tasks*: For being a task, I've designed this to be a PoC with a few hints and suggestions to something scalable. The spider runs and registers its task in `sqlite.db` with login username/id, the status of the task, and the timestamp of when it was created.
- *Semaphore*: As you guys have only two accounts available, this PoC doesn't throttle or make a pool of workers, so it executes concurrently as many `Tasks` as possible. A few features to overcome it: retry `Tasks` later, `prefetch count` etc. Tool suggestion: **RabbitMQ + Aiopika client**
- *Handle Errors and Retry*: However, the `spider.py` can at least manage its Task and retry when given certain conditions (**HTTP status as (403, 429), bypass anti-scraping methods**). Depending on the Task's result, its status in `sqlite.db` could be `Success` or some error message. Once again, for the sake of simplicity, it's stored a message instead of a status code (e.g 1=Failure, 2=Success), after all, currently, there is no way to retry failed tasks.
