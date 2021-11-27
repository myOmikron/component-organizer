import React from "./react.js";

const e = React.createElement;

export default function TextInput(props) {
    const {value, setValue, reference, ...otherProps} = props;

    return e("input", {
        ref: reference,
        value,
        onChange: (event) => {setValue(event.target.value);},
        ...otherProps,
    });
}
