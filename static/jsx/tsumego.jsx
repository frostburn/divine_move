var NBSP = "\u00a0";

var FETCH_TIMEOUT = 30000;  // Thirty seconds.

var ALPHA = ["A", "B", "C", "D", "E", "F", "G", "H", "J"];

var Cell = React.createClass({
    getInitialState: function() {
        // This hover state is supposed to help with touch devices where a touch
        // activates the element's :hover state leaving a confusing ghost stone.
        return {"hover": true};
    },
    handleClick: function(e) {
        e.preventDefault();
        this.setState({"hover": false});
        if (
            (this.props.mode === "remove" && this.props.removable) |
            (this.props.mode === "add_player" && this.props.add_player) |
            (this.props.mode === "add_opponent" && this.props.add_opponent) |
            (this.props.mode === "move" && this.props.move)
        ){
            this.props.onMove(this.props.coords);
        }
    },
    handleMouseOut: function(e) {
        e.preventDefault();
        this.setState({"hover": true});
    },
    render: function() {
        var children = [];
        var vertical = this.props.vertical;
        var horizontal = this.props.horizontal;
        var status = "";
        switch (this.props.status) {
            case "t":
                status = "target";
                break;
            case "i":
                status = "immortal";
                break;
            case "e":
                status = "escaped";
                break;
        }
        if (status == "immortal") {
            vertical = "ns";
            horizontal = "ew";
        }
        if (this.props.vertical) {
            children.push(<span className={"vertical " + vertical} key="vertical"/>);
        }
        if (this.props.horizontal) {
            children.push(<span className={"horizontal " + horizontal} key="horizontal"/>);
        }
        var color;
        switch(this.props.color) {
            case "b":
                color = "black";
                break;
            case "w":
                color = "white";
                break;
            case "k":
                color = "ko";
                break;
            default:
                color = "none";
        }
        if (color === "ko" && this.props.mode !== "move") {
            color = "none";
        }
        var color_to_play = this.props.white_to_play ? "white" : "black";
        var opponent_color = this.props.white_to_play ? "black" : "white";
        var class_name = color + " " + status + " cell-content";
        if (this.state.hover) {
            if (this.props.mode === "remove") {
                // No hover.
            }
            else if (this.props.mode == "add_player") {
                if (this.props.add_player) {
                    class_name += " " + color_to_play + "-move";
                }
            }
            else if (this.props.mode === "add_opponent") {
                if (this.props.add_opponent) {
                    class_name += " " + opponent_color + "-move";
                }
            }
            else {
                if (this.props.move) {
                    class_name += " " + color_to_play + "-move";
                }
            }
        }
        children.push(<span className={class_name} key="stone" />);
        if (this.props.last) {
            children.push(<span className="last-move" key="last" />);
        }
        return (
            <div className="cell" onClick={this.handleClick} onMouseOut={this.handleMouseOut}>
                {children}
            </div>
        );
    }
});

var Row = React.createClass({
    render: function() {
        var {data, ...rest} = this.props;
        var cells = data.map((stone) => (
            <Cell 
                color={stone.c}
                status={stone.s}
                removable={stone.r}
                vertical={stone.v}
                horizontal={stone.h}
                move={stone.m}
                add_player={stone.p}
                add_opponent={stone.o}
                coords={stone.x}
                key={stone.x}
                last={stone.l}
                {...rest}
            />
        ));
        cells.unshift(<div className="cell alpha number" key="label">{this.props.label}</div>);

        return (
            <div className="stone-row">
                {cells}
            </div>
        );
    }
});

var CoordRow = React.createClass({
    render: function() {
        var cells = [<div className="cell" key="empty" />];
        for (var i = 0; i < this.props.width; i++) {
            cells.push(<div className="cell alpha" key={ALPHA[i]}>{ALPHA[i]}</div>);
        }
        return (
            <div className="stone-row">
                {cells}
            </div>
        );
    }
});

var Board = React.createClass({
    render: function() {
        var {data, width, height, ...rest} = this.props;
        var rows = data.map((row) => (
            <Row
                data={row.stones}
                label={this.props.height - row.index}
                key={row.index}
                {...rest}
            />
        ));
        return (
            <div className="board">
                {rows}
                <CoordRow width={width} />
            </div>
        );
    }
});

var PassButton = React.createClass({
    handleClick: function(e) {
        e.preventDefault();
        this.props.onMove("pass");
    },
    render: function() {
        return <button className="btn btn-default" onClick={this.handleClick}>Pass</button>
    }
});

var Button = React.createClass({
    render: function() {
        return <button className={(this.props.className || "") + " btn btn-default"} onClick={this.props.onClick}>{this.props.label}</button>
    }
});

var LabeledCheckBox = React.createClass({
    render: function() {
        return (
            <div className="checkbox">
                <label>
                    <input type="checkbox" checked={this.props.checked} onChange={this.props.onChange} />
                    {this.props.label}
                </label>
            </div>
        );
    }
});

var RadioGroup = React.createClass({
    render: function() {
        var inputs = this.props.choices.map((choice) => (
            <div className="radio" key={choice[0]}>
                <label>
                    <input
                        type="radio"
                        name={this.props.name}
                        value={choice[0]}
                        checked={this.props.selected === choice[0]}
                        onChange={this.props.onChange.bind(null, choice[0])}
                    />
                    {choice[1]}
                </label>
            </div>
        ));
        return (
            <div>
                {inputs}
            </div>
        );
    }
});

var InlineRadioGroup = React.createClass({
    render: function() {
        var inputs = this.props.choices.map((choice) => (
            <label className="radio-inline" key={choice[0]}>
                <input
                    type="radio"
                    name={this.props.name}
                    value={choice[0]}
                    checked={this.props.selected === choice[0]}
                    onChange={this.props.onChange.bind(null, choice[0])}
                />
                {choice[1]}
            </label>
        ));
        return (
            <div>
                <strong className="pull-left inline-radio-title">{this.props.title}</strong>
                {inputs}
            </div>
        );
    }
});

var StatsPanel = React.createClass({
    render: function() {
        var data = this.props.data;
        var link = "N/A"
        if (data.active) {
            link = <a href={data.tsumego_url}>{data.url_code}</a>;
        }
        var content = [
            <p key="passes">Passes: {data.passes}</p>,
            <p key="black_captures">Captures by Black: {data.captures_by_black}</p>,
            <p key="white_captures">Captures by White: {data.captures_by_white}</p>,
        ];
        if (this.props.problem_mode) {
            content.unshift(
                <p key="ko">Ko threats: {data.ko_threats}</p>
            );
        }
        else {
            content.push(
                <p key="result">Result: {data.result}</p>
            );
            content.push(
                <p key="code">Code: {link}</p>
            );
        }
        return (
            <div className="stats-panel">
                {content}
            </div>
        );
    }
});

var StatusRow = React.createClass({
    render: function() {
        var status = this.props.status;
        if (!status.length) {
            status = NBSP;
        }
        return (
            <p>
                {status}
            </p>
        );
    }
});

var ChildResults = React.createClass({
    render: function() {
        var that = this;
        var results = this.props.results.map(function(row) {
            var coords = row[0];
            if (coords.length) {
                coords = ALPHA[coords[0]] + (that.props.height - coords[1]);
            }
            else {
                coords = "pass";
            }
            var result = row[1];
            var best = row[2];
            return (<p className={best ? "best-result" : ""} key={coords}>{coords + ": " + result}</p>);
        });
        function cmp(a, b) {
            a = a.key;
            b = b.key;
            if (a < b) {
                return -1;
            }
            else if (a > b) {
                return 1;
            }
            return 0;
        }
        results.sort(cmp);
        return (
            <div>
                {results}
            </div>
        );
    }
});

var NumberInput = React.createClass({
    handleChange: function(e) {
        this.props.onChange(e.target.value);
    },
    render: function() {
        return (
            <div className="form-group">
                <label htmlFor={this.props.label}>{this.props.label}:</label>
                <input
                    id={this.props.label}
                    className="form-control"
                    type="number"
                    value={this.props.value}
                    min={this.props.min}
                    max={this.props.max}
                    onChange={this.handleChange}
                />
            </div>
        );
    }
});

var set_problem_form_state = null;

var ProblemForm = React.createClass({
    componentDidMount: function() {
        // The rationale behind this convolution is that we want
        // the problem name to reflect the one in the DB, but we
        // still want ProblemForm to handle its own state and be
        // able the to override the DB problem.
        set_problem_form_state = (function(name, collections, dump) {
            if (dump !== this.state.dump) {
                this.setState({
                    "name": name,
                    "collections": collections,
                    "dump": dump,
                });
            }
        }).bind(this);
    },
    componentWillUnmount: function() {
        set_problem_form_state = null;
    },
    getInitialState: function() {
        return {
            "name": this.props.name,
            "collections": this.props.collections,
            "dump": this.props.dump,
            "status": "",
        };
    },
    handleNameChange: function(e) {
        this.setState({"name": e.target.value});
    },
    handleCollectionChange: function(e) {
        var options = e.target.options;
        var collections = [];
        // Options is not an Array so no .map
        for (var i = 0; i < options.length; i++) {
            if (options[i].selected) {
                collections.push(options[i].value);
            }
        }
        this.setState({"collections": collections});
    },
    handleSubmit: function(e) {
        e.preventDefault();
        if (!this.props.active) {
            return;
        }
        var name = (this.state.name || "").trim();
        var collections = this.state.collections;
        var payload = {
            "action": "add_problem",
            "dump": this.state.dump,
            "name": name,
            "collections": collections
        };
        var that = this;
        fetch(window.json_url, {
            method: "post",
            credentials: "include",
            body: JSON.stringify(payload)
        })
        .then(to_json)
        .then(
            function(data) {
                if (data.success) {
                    that.setState({"status": data.success});
                    setTimeout(function() {
                        that.setState({"status": ""});
                    }, 2000);
                }
                else if (data.error) {
                    that.setState({"status": data.error});
                }
                else {
                    that.setState({"status": "Unknown error saving problem."});
                }
            }
        )
        .catch(
            function(error) {
                that.setState({"status": "Error: " + error});
            }
        );
    },
    render: function() {
        var options = this.props.options.map((option) => (
            <option key={option.value} value={option.value}>{option.name}</option>
        ));
        var class_name = this.props.hidden ? "hidden" : "";
        return (
            <form className={class_name} onSubmit={this.handleSubmit}>
                <div className="form-group">
                    <label htmlFor="problem_name">Name:</label>
                    <input
                        type="text"
                        className="form-control"
                        id="problem_name"
                        placeholder="Problem name"
                        value={this.state.name}
                        onChange={this.handleNameChange}
                    />
                    <label htmlFor="collections">Collections:</label>
                    <select
                        multiple={true}
                        className="form-control"
                        value={this.state.collections}
                        onChange={this.handleCollectionChange}
                    >
                        {options}
                    </select>
                </div>
                <input type="submit" className="btn btn-default" disabled={!this.props.active} value="Submit" />
                <span className="problem-status">{this.state.status}</span>
            </form>
        );
    }
});

function handle_status(response) {
    if (response.status >= 200 && response.status < 300) {
        return Promise.resolve(response);
    } else {
        return Promise.reject(new Error(response.statusText));
    }
}

function to_json(response) {
    return response.json();
}

function handle_error(data) {
    if ("error" in data) {
        return Promise.reject(new Error(data.error));
    }
    return Promise.resolve(data);
}

var Game = React.createClass({
    doFetch: function(params, dump, captures) {
        var active = dump ? true : this.state.data.active;
        if (params.length && !active) {
            if (this.props.debug) {
                console.log("Not fetching", params, active);
            }
            return;
        }
        if (this.block_fetch) {
            return;
        }
        this.block_fetch = true;
        var that = this;
        // Not a real timeout that cancels the request.
        // It just lifts the block for new fetches with undefined behavior. (The last completed fetch stays in effect.)
        var fetch_timeout = setTimeout(function () {
            that.block_fetch = false;
        }, FETCH_TIMEOUT);
        if (this.state.value) {
            params += "&value=1";
        }
        if (this.state.problem_mode) {
            params += "&problem=1";
        }
        if (typeof dump === "undefined") {
            dump = this.state.data.dump;
            captures = this.state.data.captures;
        }
        fetch(window.json_url + "?dump=" + escape(dump) + "&captures=" + escape(captures) + params)
        .then(
            function(response) {
                that.block_fetch = false;
                clearTimeout(fetch_timeout);
                return Promise.resolve(response);
            }
        )
        .then(handle_status)
        .then(to_json)
        .then(handle_error)
        .then(
            function(data) {
                if (that.props.debug) {
                    console.log(data);
                }
                that.setState({"data": data});
                set_problem_form_state(data.problem_name, data.problem_collections, data.dump);
                if (data.problem_failed || data.problem_solved) {
                    that.setState({"problem_mode": false});
                    that.updateElo(!!data.problem_solved);
                }
            }
        )
        .catch(
            function(error) {
                that.setState({
                    "user_status": "Request failed",
                    "problem_status": String(error),
                });
            }
        );
    },
    updateElo: function(success) {
        var payload = {
            "action": "update_elo",
            "success": success,
            "dump": this.props.data.dump,
        };
        var that = this;
        fetch(window.json_url, {
            method: "post",
            credentials: "include",
            body: JSON.stringify(payload)
        })
        .then(to_json)
        .then(
            function(data) {
                var user_status = "User: " + data.user_elo + " (" + data.user_delta + ")";
                var problem_status = data.problem_name + ": " + data.problem_elo + " (" + data.problem_delta + ")";
                that.setState({
                    "user_status": user_status,
                    "problem_status": problem_status,
                });
                $("#user_elo").text(data.navbar_elo);
            }
        )
        .catch(
            function(error) {
                that.setState({
                    "user_status": "Request failed",
                    "problem_status": String(error),
                });
            }
        );
    },
    pushUndo: function() {
        if (this.state.data.active) {
            var undos = this.state.undos;
            undos.push([this.state.data.dump, this.state.data.captures]);
            this.setState({"undos": undos});
        }
    },
    handleUndo: function() {
        var undos = this.state.undos;
        if (undos.length) {
            var undo = undos.pop()
            this.doFetch("", undo[0], undo[1]);
        }
    },
    handleMove: function(coords) {
        this.pushUndo();
        var params = "&" + this.state.mode + "=" + escape(coords);
        if (this.state.vs_book && this.state.mode === "move") {
            params += "&vs_book=1";
        }
        this.doFetch(params);
    },
    handleSwap: function() {
        // Have to force update to prevent the UI from blinking as fetch takes a while.
        if (this.state.mode === "add_player") {
            this.setState({"mode": "add_opponent"});
            this.forceUpdate();
        }
        else if (this.state.mode === "add_opponent") {
            this.setState({"mode": "add_player"});
            this.forceUpdate();
        }
        this.doFetch("&swap=1");
    },
    handleBook: function() {
        this.pushUndo();
        var params = "&book=1";
        if (this.state.vs_book) {
            params += "&vs_book=1";
        }
        this.doFetch(params);
    },
    handleValueChange: function() {
        // Have to mutate here so that doFetch works correctly.
        this.state.value = !this.state.value;
        this.setState({"value": this.state.value});
        this.doFetch("");
    },
    handleVsBookChange: function() {
        this.setState({"vs_book": !this.state.vs_book});
    },
    handleColorChange: function() {
        this.doFetch("&color=1");
    },
    handleModeChange: function(mode) {
        this.setState({"mode": mode});
    },
    handleKoThreatsChange: function(value) {
        this.doFetch("&ko_threats=" + value);
    },
    handleReset: function() {
        this.doFetch("", this.props.data.dump, this.props.data.captures);
        this.setState({
            "undos": [],
        });
    },
    handleSkip: function() {
        this.setState({
            "problem_mode": false,
        });
        this.doFetch("");  // Updates the title.
    },
    handleNext: function() {
        var payload = {
            "action": "next_problem",
        };
        var that = this;
        fetch(window.json_url, {
            method: "post",
            credentials: "include",
            body: JSON.stringify(payload)
        })
        .then(to_json)
        .then(
            function(data) {
                if (data.success) {
                    window.location.href = data.href;
                }
                else {
                    that.setState({
                        "user_status": "You have tried all the available problems.",
                        "problem_status": "",
                    });
                }
            }
        )
        .catch(
            function(error) {
                that.setState({
                    "user_status": "Request failed",
                    "problem_status": String(error),
                });
            }
        );
    },
    getInitialState: function() {
        return {
            "data": this.props.data,
            "vs_book": true,
            "value": false,
            "mode": "move",
            "undos": [],
            "problem_mode": this.props.problem_mode,
            "user_status": "",
            "problem_status": "",
        };
    },
    render: function() {
        var mode_options;
        var mode_labels = ["Move", "Add Black", "Add White", "Remove"];
        if (this.state.data.white_to_play) {
            mode_options = ["move", "add_opponent", "add_player", "remove"];
        }
        else {
            mode_options = ["move", "add_player", "add_opponent", "remove"];
        }
        var mode_choices = [];
        for (var i = 0; i < 4; i++) {
            mode_choices.push([mode_options[i], mode_labels[i]]);
        }
        var child_results = [];
        if (typeof this.state.data.value !== "undefined") {
            child_results = this.state.data.value.children;
        }
        var ko_threat_choices = [];
        for (var i = this.state.data.min_ko_threats; i <= this.state.data.max_ko_threats; i++) {
            ko_threat_choices.push([i, i]);
        }
        var title = this.state.data.title;
        if (this.state.problem_mode) {
            title = this.props.data.title;
        }
        if (!title.length) {
            title = NBSP;
        }

        var extra_move_buttons = [];
        var edit_controls = [];
        var reset_button = null;
        var skip_button = null;
        if (this.state.problem_mode) {
            skip_button = <Button key="skip" label="Skip to edit mode" onClick={this.handleSkip} />
        }
        else {
            extra_move_buttons = [
                <Button key="undo" label="Undo" onClick={this.handleUndo} />,
                <Button key="book" label="Book move" onClick={this.handleBook} />,
            ];
            edit_controls = [
                <Button key="swap" label="Swap players" onClick={this.handleSwap} />,
                <Button key="color" label="Swap colors" onClick={this.handleColorChange} />,
                <LabeledCheckBox key="result" label="Show result" checked={this.state.value} onChange={this.handleValueChange} />,
                <LabeledCheckBox key="vs_book" label="Play against the book" checked={this.state.vs_book} onChange={this.handleVsBookChange} />,
                <InlineRadioGroup key="ko" title="Ko threats:" choices={ko_threat_choices} selected={this.state.data.ko_threats} onChange={this.handleKoThreatsChange} />,
                <RadioGroup key="mode" choices={mode_choices} selected={this.state.mode} onChange={this.handleModeChange} />,
            ];
            reset_button = <Button key="reset" label="Reset" onClick={this.handleReset} />
        }
        return (
            <div className="game row">
                <div className="col-md-5">
                    <h3>{title}</h3>
                    <Board
                        data={this.state.data.rows}
                        onMove={this.handleMove}
                        mode={this.state.mode}
                        white_to_play={this.state.data.white_to_play}
                        width={this.props.data.width}
                        height={this.props.data.height}
                    />
                    <StatusRow status={this.state.data.status} />
                    <PassButton onMove={this.handleMove} />
                    {extra_move_buttons}
                    <ProblemForm
                        name={this.props.data.problem_name}
                        collections={this.props.data.problem_collections}
                        dump={this.props.data.dump}
                        options={this.props.problem_options}
                        active={this.state.data.active}
                        hidden={this.state.problem_mode}  // Hidden instead of removed due to mounting issues.
                    />
                </div>
                <div className="col-md-3">
                    {edit_controls}
                    <StatsPanel data={this.state.data} problem_mode={this.state.problem_mode} />
                    {skip_button}
                    {reset_button}
                    <Button className="next-problem" label="Next problem" onClick={this.handleNext} />
                </div>
                <div className="col-md-4">
                    <p>{this.state.user_status}</p>
                    <p>{this.state.problem_status}</p>
                    <ChildResults results={child_results} height={this.props.data.height} />
                </div>
            </div>
        );
    }
});


ReactDOM.render(
    <Game
        data={window.state}
        problem_options={window.problem_options}
        problem_mode={window.problem_mode}
        debug={window.debug}
    />,
    document.getElementById("container")
);
