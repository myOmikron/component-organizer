import React from "./react.js";

const e = React.createElement;

export class ContainerTree extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            openContainers: {},
        };
        for (const ct in this.props.containers) {
            this.state.openContainers[ct] = false;
        }
        this.state.openContainers[this.props.root] = true;
        for (let i = 0; i < this.props.initiallyOpened.length; i++) {
            let ct = this.props.initiallyOpened[i];
            while (ct !== this.props.root) {
                this.state.openContainers[ct] = true;
                ct = this.props.containers[ct].parent;
            }
        }
    }

    renderContainer(ct) {
        const setState = this.setState.bind(this);
        const {name, children} = this.props.containers[ct];
        const {openContainer, createContainer} = this.props;

        function CreateContainer({ct}) {
            if (createContainer) {
                return e("tr", {}, [
                    e("td"), e("td"),
                    e("td", {onClick() {createContainer(ct);}, style: {cursor: "pointer"}, className: "darker"}, [
                        e("img", {src: "/static/img/star.svg", width: 26, height: 20}),
                        "Create new entry here"
                    ]),
                ]);
            } else {
                return null;
            }
        }

        return e("table", {className: "container-tree"}, [
            e("tr", {}, [
                e("td", {
                    colSpan: 2,
                    onClick() {
                        setState((state) => ({
                            openContainers: {
                                ...state.openContainers,
                                [ct]: !state.openContainers[ct],
                            }
                        }));
                    },
                }, e("img", {src: "/static/img/caret_down.svg", className: this.state.openContainers[ct] ? "" : "closed-caret"})),
                e("td", {
                    onClick() {
                        openContainer(ct);
                        setState((state) => ({
                            openContainers: {
                                ...state.openContainers,
                                [ct]: true,
                            }
                        }));
                    },
                }, name),
            ]),
            ...(this.state.openContainers[ct] ? [e(CreateContainer, {ct,}), ...children.map(
                (child) => e("tr", {}, [
                    e("td"), e("td"),
                    e("td", {}, this.renderContainer(child))
                ])
            )] : []),
        ]);
    }

    render() {
        return this.renderContainer(this.props.root);
    }
}
ContainerTree.defaultProps = {
    createContainer: null,  // function (ct) {console.log("Created new container inside container with id: ", ct);}
    openContainer: function (ct) {console.log("Opened container with id: ", ct);},
    root: 0,
    initiallyOpened: [],
    containers: {
        0: {
            name: "Dummy Root",
            children: [],
            parent: 0,
        }
    }
};

function _clamp(min, value, max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

export class SplitScreen extends React.Component {

    static PHI = (1 + Math.sqrt(5)) / 2;

    constructor(props) {
        super(props);

        this.state = {
            seperatorPosition: (1 - 1 / SplitScreen.PHI) * 100,  // position of seperator in % of this
            grabbedSeperator: false,
        };
        this.outerDiv = React.createRef();
    }

    render() {
        const {seperatorWidth, splitVertical} = this.props;
        const {seperatorPosition} = this.state;
        const [leftChild, rightChild] = this.props.children;
        const setState = this.setState.bind(this);

        const width = splitVertical ? "width" : "height";
        const height = splitVertical ? "height" : "width";
        const left = splitVertical ? "left" : "top";

        return e("div", {
            key: "outerDiv",
            ref: this.outerDiv,
            style: {
                position: "relative",
                width: "100vw",
                height: "100vh",
            },
            onMouseMove: this.state.grabbedSeperator ? function ({clientX, clientY, buttons, ...event}) {
                if (buttons & 1) {
                    const {clientWidth, clientHeight, clientLeft, clientTop} = this.outerDiv.current;

                    const x = splitVertical ? clientX : clientY;
                    const width = splitVertical ? clientWidth : clientHeight;
                    const left = splitVertical ? clientLeft : clientTop;
                    setState({seperatorPosition: _clamp(10, (x - left) / width * 100, 90)});
                } else {
                    setState({grabbedSeperator: false});
                }
            }.bind(this) : undefined,
        }, [
            e("div", {
                key: "rightChild",
                style: {
                    position: "absolute",
                    overflow: "hidden",
                    [height]: "100%",
                    [left]: 0,
                    [width]: `calc(${seperatorPosition}% - ${seperatorWidth} / 2)`,
                },
            }, leftChild),
            e("div", {
                key: "seperator",
                style: {
                    position: "absolute",
                    cursor: splitVertical ? "ew-resize" : "ns-resize",
                    [height]: "100%",
                    [left]: `calc(${seperatorPosition}% - ${seperatorWidth} / 2)`,
                    [width]: seperatorWidth,
                },
                className: "seperator",
                onMouseDown() { setState({grabbedSeperator: true}); },
            }),
            e("div", {
                key: "leftChild",
                style: {
                    position: "absolute",
                    overflow: "hidden",
                    [height]: "100%",
                    [left]: `calc(${seperatorPosition}% + ${seperatorWidth} / 2)`,
                    [width]: `calc(${100 - seperatorPosition}% - ${seperatorWidth} / 2)`,
                }
            }, rightChild)]);
    }
}
SplitScreen.defaultProps = {
    seperatorWidth: "0.1em",
    splitVertical: true,
};
