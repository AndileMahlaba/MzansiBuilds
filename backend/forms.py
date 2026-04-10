from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import Email, InputRequired, Length, Optional

from backend.constants import PROJECT_STAGES


def _stage_choices() -> list[tuple[str, str]]:
    labels = {
        "idea": "Idea",
        "planning": "Planning",
        "development": "Development",
        "testing": "Testing",
    }
    return [(s, labels.get(s, s.title())) for s in PROJECT_STAGES]


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired(), Length(max=120)])
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=128)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Log in")


class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save changes")


class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired(), Length(min=2, max=200)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=20000)])
    stage = SelectField("Stage", choices=_stage_choices(), validators=[InputRequired()])
    support_needed = StringField(
        "Support needed", validators=[Optional(), Length(max=200)]
    )
    submit = SubmitField("Publish project")


class CommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[InputRequired(), Length(max=5000)])
    submit = SubmitField("Post comment")


class CollaborateForm(FlaskForm):
    message = TextAreaField(
        "Message (optional)", validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField("Raise hand to collaborate")


class MilestoneForm(FlaskForm):
    title = StringField("Milestone", validators=[InputRequired(), Length(min=2, max=200)])
    description = TextAreaField("Details", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("Add milestone")


class CompleteProjectForm(FlaskForm):
    submit = SubmitField("Mark project as complete")
