import streamlit as st
import openai

# Replace with your own or secure way of storing the API key
openai.api_key = st.secrets["OPENAI_API"]
# Replace with your actual logo image URL or file path
LOGO_URL = "https://cdn.sanity.io/images/bbnkhnhl/production/1f317b00397c3c318af21aa8978d53aacf8b69c8-3449x322.svg"


def generate_code_snippet(user_inputs):
    """
    Builds the base Python code with a dynamic `inputs` array
    based on user inputs.
    """
    base_code = """# from langflow.field_typing import Data
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data


class CustomComponent(Component):
    display_name = "Custom Component"
    description = "Use as a template to create your own component."
    documentation: str = "http://docs.langflow.org/components/custom"
    icon = "code"
    name = "CustomComponent"

    inputs = [
        # This is where we customize based on user inputs
    ]

    outputs = [
        Output(display_name="Output", name="output", method="build_output"),
    ]

    def build_output(self) -> Data:
        data = Data(value=self.input_value)
        self.status = data
        return data
"""

    inputs_str = []
    for inp in user_inputs:
        block = f"""MessageTextInput(
            name="{inp['name']}",
            display_name="{inp['display_name']}",
            info="{inp['description']}",
            value="",  # you can customize a default value if desired
            tool_mode=True,
        )"""
        inputs_str.append(block)

    # Join them with commas & indentation
    inputs_code_str = ",\n        ".join(inputs_str)

    # Insert into the base code
    final_code = base_code.replace(
        "# This is where we customize based on user inputs",
        inputs_code_str
    )

    return final_code


def ask_gpt_for_code(user_inputs):
    """
    Optionally calls GPT to refine or validate the generated code.
    Returns only the final code from the GPT response.
    """
    code_snippet = generate_code_snippet(user_inputs)

    system_prompt = (
        "You are an assistant that helps produce Python code for a custom "
        "Langflow Component with a dynamic inputs array."
    )
    user_prompt = (
        "Please review the following code snippet. Adjust if necessary to ensure "
        "it's valid Python code:\n\n"
        f"{code_snippet}\n\n"
        "Return only the final code. Do not include extra explanations."
    )

    # You can change this to a different model as needed
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )
    final_code = response.choices[0].message.content.strip()
    return final_code


def main():
    # Create two tabs: one for the form, one for the code
    tab_form, tab_code = st.tabs(["Component Generator", "Generated Code"])

    with tab_form:
        st.sidebar.image(LOGO_URL, use_column_width=True)
        st.title("Custom Langflow Component Generator")

        # Footer
        st.markdown(
            """
            <style>
            .footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                text-align: center;
                background: #f5f5f5;
                padding: 0.5rem;
                font-weight: bold;
                z-index: 9999;
            }
            </style>
            <div class="footer">
                Built with Langflow and DataStax
            </div>
            """,
            unsafe_allow_html=True
        )

        num_inputs = st.sidebar.slider("How many inputs do you want?", 0, 10, 1)

        with st.form("dynamic_form"):
            for i in range(num_inputs):
                cols = st.columns(2)
                with cols[0]:
                    st.text_input(f"Name {i + 1} (unique, no spaces)", key=f"name_{i}")
                with cols[1]:
                    st.text_input(f"Display Name {i + 1}", key=f"display_name_{i}")

                st.text_area(f"Description {i + 1}", key=f"description_{i}")

            # Center the submit button
            col_left, col_mid, col_right = st.columns([2, 1, 2])
            with col_mid:
                submitted = st.form_submit_button("Submit")

        # After submit, validate & generate code
        if submitted:
            unique_names = set()
            has_error = False
            user_data = []

            for i in range(num_inputs):
                name = st.session_state.get(f"name_{i}", "")
                display_name = st.session_state.get(f"display_name_{i}", "")
                description = st.session_state.get(f"description_{i}", "")

                if not name:
                    st.error(f"Name of Input {i + 1} cannot be empty.")
                    has_error = True
                if " " in name:
                    st.error(f"Name of Input {i + 1} ('{name}') contains spaces. Spaces are not allowed.")
                    has_error = True
                if name in unique_names:
                    st.error(f"Name of Input {i + 1} ('{name}') is a duplicate. Each name must be unique.")
                    has_error = True
                else:
                    unique_names.add(name)

                user_data.append(
                    {
                        "name": name,
                        "display_name": display_name,
                        "description": description,
                    }
                )

            if has_error:
                st.warning("Please fix the errors above and resubmit.")
                st.stop()

            with st.spinner("Generating custom component code"):
                final_code = ask_gpt_for_code(user_data)
                # final_code = "``````python\n" + final_code + "\n``````"

            # Store the final code in session_state so it can be viewed in the other tab
            st.session_state["final_code"] = final_code

            # Give a quick success message or direct user to the code tab
            st.success("Code generated! Go to the 'Generated Code' tab to view it.")

    with tab_code:
        # If code has been generated, display it. Otherwise, show info.
        final_code = st.session_state.get("final_code", None)
        # final_code = final_code.lstrip("```python")
        # final_code = final_code.rstrip("```")
        if final_code:
            # We use st.code(...) for syntax highlighting or st.write(...) if you prefer raw.
            st.write(final_code)
        else:
            st.info("No code generated yet. Go to the 'Component Generator' tab and submit the form.")


if __name__ == "__main__":
    main()
