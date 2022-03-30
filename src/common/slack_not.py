from typing import TYPE_CHECKING, Any, Callable, Union, cast
from src.common.azure_key_vault_task import KeyVaultTask
from toolz import curry
import os, json
import prefect

if TYPE_CHECKING:
    import prefect.engine.state
    import prefect.client
    from prefect import Flow, Task  # noqa

TrackedObjectType = Union["Flow", "Task"]

__all__ = ["callback_factory", "slack_notifier"]


def callback_factory(
    fn: Callable[[Any, "prefect.engine.state.State"], Any],
    check: Callable[["prefect.engine.state.State"], bool],
) -> Callable:
    """
    Utility for generating state handlers that serve as callbacks, under arbitrary
    state-based checks.
    Args:
        - fn (Callable): a function with signature `fn(obj, state: State) -> None`
            that will be called anytime the associated state-check passes; in general, it is
            expected that this function will have side effects (e.g., sends an email).  The
            first argument to this function is the `Task` or `Flow` it is attached to.
        - check (Callable): a function with signature `check(state: State) -> bool`
            that is used for determining when the callback function should be called
    Returns:
        - state_handler (Callable): a state handler function that can be attached to both Tasks
            and Flows
    Example:
        ```python
        from prefect import Task, Flow
        from prefect.utilities.notifications import callback_factory
        fn = lambda obj, state: print(state)
        check = lambda state: state.is_successful()
        callback = callback_factory(fn, check)
        t = Task(state_handlers=[callback])
        f = Flow(tasks=[t], state_handlers=[callback])
        f.run()
        # prints:
        # Success("Task run succeeded.")
        # Success("All reference tasks succeeded.")
        ```
    """

    def state_handler(
        obj: Any,
        old_state: "prefect.engine.state.State",
        new_state: "prefect.engine.state.State",
    ) -> "prefect.engine.state.State":
        if check(new_state) is True:
            fn(obj, new_state)
        return new_state

    return state_handler


def slack_message_formatter(
    tracked_obj: TrackedObjectType,
    state: "prefect.engine.state.State",
    backend_info: bool = True,
) -> dict:
    # see https://api.slack.com/docs/message-attachments
    fields = []
    if isinstance(state.result, Exception):
        value = "```{}```".format(repr(state.result))
    else:
        value = cast(str, state.message)
    if value is not None:
        fields.append({"title": "Message", "value": value, "short": False})

    notification_payload = {
        "fallback": "State change notification",
        "color": state.color,
        "author_name": "Prefect",
        "author_link": "https://www.prefect.io/",
        "author_icon": "https://emoji.slack-edge.com/TAN3D79AL/prefect/2497370f58500a5a.png",
        "title": type(state).__name__,
        "fields": fields,
        #                "title_link": "https://www.prefect.io/",
        "text": "{0} is now in a {1} state".format(
            tracked_obj.name, type(state).__name__
        ),
        "footer": "Prefect notification",
    }

    if backend_info and prefect.context.get("flow_run_id"):
        #url = None

        """if isinstance(tracked_obj, prefect.Flow):
            url = prefect.client.Client().get  .get_cloud_url(
                "flow-run", prefect.context["flow_run_id"], as_user=False
            )
        elif isinstance(tracked_obj, prefect.Task):
            url = prefect.client.Client().get_cloud_url(
                "task-run", prefect.context.get("task_run_id", ""), as_user=False
            )

        if url:
            notification_payload.update(title_link=url)"""

    data = {"attachments": [notification_payload]}
    return data

@curry
def slack_notifier(
    tracked_obj: TrackedObjectType,
    old_state: "prefect.engine.state.State",
    new_state: "prefect.engine.state.State",
    ignore_states: list = None,
    only_states: list = None,
    webhook_secret: str = None,
    backend_info: bool = True,
) -> "prefect.engine.state.State":
    """
    Slack state change handler; requires having the Prefect slack app installed.  Works as a
    standalone state handler, or can be called from within a custom state handler.  This
    function is curried meaning that it can be called multiple times to partially bind any
    keyword arguments (see example below).
    Args:
        - tracked_obj (Task or Flow): Task or Flow object the handler is
            registered with
        - old_state (State): previous state of tracked object
        - new_state (State): new state of tracked object
        - ignore_states ([State], optional): list of `State` classes to ignore, e.g.,
            `[Running, Scheduled]`. If `new_state` is an instance of one of the passed states,
            no notification will occur.
        - only_states ([State], optional): similar to `ignore_states`, but instead _only_
            notifies you if the Task / Flow is in a state from the provided list of `State`
            classes
        - webhook_secret (str, optional): the name of the Prefect Secret that stores your slack
            webhook URL; defaults to `"SLACK_WEBHOOK_URL"`
        - backend_info (bool, optional): Whether to supply slack notification with urls
            pointing to backend pages; defaults to True
    Returns:
        - State: the `new_state` object that was provided
    Raises:
        - ValueError: if the slack notification fails for any reason
    Example:
        ```python
        from prefect import task
        from prefect.utilities.notifications import slack_notifier
        @task(state_handlers=[slack_notifier(ignore_states=[Running])]) # uses currying
        def add(x, y):
            return x + y
        ```
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", None)
    ignore_states = ignore_states or []
    only_states = only_states or []

    if any(isinstance(new_state, ignored) for ignored in ignore_states):
        return new_state

    if only_states and not any(
            [isinstance(new_state, included) for included in only_states]
    ):
        return new_state

    # 'import requests' is expensive time-wise, we should do this just-in-time to keep
    # the 'import prefect' time low
    import requests

    form_data = slack_message_formatter(tracked_obj, new_state, backend_info)
    r = requests.post(webhook_url, json=form_data)
    if not r.ok:
        raise ValueError("Slack notification for {} failed".format(tracked_obj))
    return new_state
