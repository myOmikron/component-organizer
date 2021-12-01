import React from "./react.js";

const e = React.createElement;

// equals n % m but always positive
function modulo(n, m) {
    let result = n % m;
    result = result < 0 ? result + m : result;
    return result;
}

export default function TextInput(props) {
    const {value, setValue, reference, ...otherProps} = props;

    return e("input", {
        ref: reference,
        value,
        onChange: (event) => {setValue(event.target.value);},
        ...otherProps,
    });
}

export function AutoComplete(props) {
    const {key, focused, complete, options, index, setIndex, reference, ...otherProps} = props;
    const internalReference = React.useRef(null);
    const input = reference ? reference : internalReference;
    function updateIndex(delta) {
        setIndex(modulo(index + delta + 1, options.length + 1) - 1);
    }

    return e(React.Fragment, {key}, [
        e(TextInput, {
            key: "input",
            reference: input,
            onKeyDown(event) {
                if (focused) {
                    const {key} = event;
                    if (key === "ArrowDown")
                        updateIndex(+1);
                    else if (key === "ArrowUp")
                        updateIndex(-1);
                    else if (key === "Tab") {
                        if (options.length > 1)
                            updateIndex(+1);
                        else {
                            setIndex(0);
                            complete();
                        }
                        event.preventDefault();
                    }
                    else if (key === "Enter") {
                        if (complete()) {
                            event.preventDefault();
                        }
                    }
                }
            },
            ...otherProps,
        }),
        input && focused && options && options.length > 0 ?  e("div", {
            key: "dropdown",
            style: {
                position: "fixed",
                left: input.offsetLeft + "px",
                top: input.offsetTop + input.offsetHeight + "px",
                background: "#15202b",
                border: "1px solid",
                margin: "5px",
            }
        }, options.map((key, i) => e("div", {
            style: {
                padding: "2px",
                background: i === index ? "#1f2f3f" : "",
                cursor: "pointer",
            },
            onMouseEnter() {setIndex(i);},
            onMouseDown() {complete();},
        }, key))) : null,
    ]);
}