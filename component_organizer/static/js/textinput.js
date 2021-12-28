import React from "./react.js";
import {request} from "./async.js";

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

export function LazyAutocomplete(props) {
    const {url, value, setValue, ...otherProps} = props;
    const [index, setIndex] = React.useState(-1);
    const [focused, setFocused] = React.useState(false);
    const [active, setActive] = React.useState(false);  // has the input been focus on (at least once)
    const [options, setOptions] = React.useState(null); // all options to choose from
    const [filteredOptions, setFilteredOptions] = React.useState([]); // options which still match current value

    React.useEffect(function() {
        if (!active && focused) {
            setActive(true);
        }
    }, [focused]);
    React.useEffect(function() {
        if (active) {
            request(url).then(function (options) {setOptions(options);})
        }
    }, [url, active]);
    React.useEffect(function () {
        if (options !== null) {
            const lowerValue = ("" + value).toLowerCase();
            setFilteredOptions(options.filter((option) => ("" + option).toLowerCase().startsWith(lowerValue)));
        }
    }, [options, value]);

    function complete() {
        if (index < 0 || index >= filteredOptions.length) return;
        setValue(filteredOptions[index]);
    }

    return e(AutoComplete, {
        focused,
        complete,
        options: filteredOptions,
        index, setIndex,
        value, setValue,
        onFocus() {setFocused(true);},
        onBlur() {setFocused(false);},
        ...otherProps,
    });
}

export function AddKeyRow(props) {
    const {addField} = props;
    const reference = React.useRef(null);
    const [field, setField] = React.useState("");
    const [type, setType] = React.useState("string");
    function wrappedAddField(event) {
        if (event) {
            event.preventDefault();
        }
        if (addField(field, type)) {
            setField("");
            if (reference.current) {reference.current.focus();}
        }
    }

    return e("tr", {}, [
        e("td", {}, e("select", {
            value: type,
            onChange(event) {
                setType(event.target.value);
            },
        }, [
            e("option", {value: "string"}, "String"),
            e("option", {value: "number"}, "Number"),
            e("option", {value: "unit"}, "Number with Unit"),
            e("option", {value: "file"}, "File"),
        ])),
        e("td", {}, e("form", {
            onSubmit: wrappedAddField,
        }, e("label", {}, e(LazyAutocomplete, {
            url: "/api/common_keys",
            value: field,
            setValue: setField,
            reference,
        })))),
        e("td", {}, e("button", {
            onClick: wrappedAddField,
        }, "Add")),
    ]);
}
