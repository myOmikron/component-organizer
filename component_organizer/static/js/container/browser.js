import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {ContainerTree, SplitScreen} from "../trees.js";

const e = React.createElement;

class Browser extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            openContainer: this.props.root,
        };
    }

    render() {
        const setState = this.setState.bind(this);

        return e(SplitScreen, {}, [
            e(ContainerTree, {
                openContainer(ct) {
                    setState({openContainer: ct});
                },
                ...this.props
            }),
            e(React.Fragment, {}, [
                e("link", {rel: "stylesheet", href: "/static/css/container/browser.css"}),
                e("div", {className: "flex-horizontal"}, [
                    ...this.props.containers[this.state.openContainer].children.map((ct) =>
                        e("a", {href: "/browse/container/" + ct}, e("div", {className: "item-box"}, [e("img", {className: "icon", alt: "Folder", src: "/static/img/folder.svg"}), e("br"), this.props.containers[ct].name])),
                    ),
                    e("a", {href: "/browse/container/" + this.state.openContainer + "/new"}, e("div", {className: "item-box"}, [e("img", {className: "icon", alt: "New Folder", src: "/static/img/new_folder.svg"}), e("br"), "Add new container"])),
                    /*{% for item in items %}
                    <a href="">
                        <div class="item-box">
                            <img class="icon" src="{% static 'img/file.svg' %}" alt="File"> <br/>
                            {{ item.item }}
                        </div>
                    </a>
                    {% endfor %}*/
                ]),
            ]),
            this.state.openContainer,
        ]);
    }
}

ReactDOM.render(e(Browser, document.props), document.getElementById("root"));
