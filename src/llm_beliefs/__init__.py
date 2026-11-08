# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026  Philipp Emanuel Weidmann <pew@worldwidemann.com> + contributors

import sys
from pathlib import Path

import pycountry
from openai import OpenAI


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent.parent
    map_svg = (project_dir / "blank-map.svg").read_text(encoding="utf-8")

    client = OpenAI()

    model = sys.argv[1]
    question = sys.argv[2]

    yes_countries = []
    no_countries = []
    other_countries = []

    for country in pycountry.countries:
        country_name = country.name
        name_parts = country_name.split(", ")
        if len(name_parts) == 2 and " of" in name_parts[1]:
            # Transform to more common representation,
            # e.g. "Korea, Democratic People's Republic of" -> "the Democratic People's Republic of Korea"
            country_name = f"the {name_parts[1]} {name_parts[0]}"

        country_question = question.replace("[country]", country_name)
        prompt = (
            f'{country_question} Respond only with the word "Yes" or the word "No".'
        )

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
            extra_body={
                "reasoning": {
                    "effort": "minimal",
                    "exclude": True,
                }
            },
        )

        response = completion.choices[0].message.content

        if response is None:
            raise ValueError("response is None")

        if response.startswith("Yes"):
            yes_countries.append(country)
        elif response.startswith("No"):
            no_countries.append(country)
        else:
            other_countries.append(country)

        print(f"{country_question} -> {response}")

    yes_classes = ", ".join(f".{c.alpha_2.lower()}" for c in yes_countries)
    no_classes = ", ".join(f".{c.alpha_2.lower()}" for c in no_countries)
    other_classes = ", ".join(f".{c.alpha_2.lower()}" for c in other_countries)

    country_styles = f"""{yes_classes}
{{
    fill: #0066ff;
}}

{no_classes}
{{
    fill: #ff6600;
}}

{other_classes}
{{
    fill: #000000;
}}"""

    map_svg = map_svg.replace("###COUNTRY_STYLES###", country_styles)
    map_svg = map_svg.replace("###QUESTION###", question)
    map_svg = map_svg.replace("###MODEL###", model)

    question_fragment = "".join(
        [c for c in question.lower().replace(" ", "-") if c.isalpha() or c == "-"]
    )
    model_fragment = model.lower().replace("/", "--")
    output_filename = f"{question_fragment}_{model_fragment}.svg"

    (project_dir / "maps" / output_filename).write_text(map_svg, encoding="utf-8")
