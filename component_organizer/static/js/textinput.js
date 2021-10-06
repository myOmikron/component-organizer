import React from "./react.js";

const e = React.createElement;

export default function TextInput(props) {
    const {value, setValue, ...otherProps} = props;

    return e("input", {
        value,
        onChange: (event) => {setValue(event.target.value);},
        ...otherProps,
    });
}
