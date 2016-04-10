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
        if (this.props.mode === "remove") {
            this.props.onMove(this.props.coords);
        }
        if (this.props.mode === "add_opponent") {
            if (this.props.o_move) {
                this.props.onMove(this.props.coords);
                return;
            }
        }
        else if (this.props.move) {
            this.props.onMove(this.props.coords);
            return;
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
        var color_to_play = this.props.white_to_play ? "white" : "black";
        var opponent_color = this.props.white_to_play ? "black" : "white";
        var class_name = color + " " + status + " cell-content";
        if (this.state.hover) {
            if (this.props.mode === "add_opponent") {
                if (this.props.o_move) {
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
                vertical={stone.v}
                horizontal={stone.h}
                move={stone.m}
                o_move={stone.o}
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
        return <button className="btn btn-default" onClick={this.props.onClick}>{this.props.label}</button>
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
        return (
            <p>
                Passes: {data.passes}<br />
                Captures by Black: {data.captures_by_black}<br />
                Captures by White: {data.captures_by_white}<br />
                Result: {data.result}<br />
                Code: <a href={data.tsumego_url}>{data.code}</a>
            </p>
        );
    }
});

var StatusRow = React.createClass({
    render: function() {
        var status = this.props.status;
        if (!status.length) {
            status = "\u00a0";
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
            "dump": this.props.dump
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
        var name = this.state.name.trim();
        var collections = this.state.collections;
        var payload = {
            "action": "add_problem",
            "dump": this.state.dump,
            "name": name,
            "collections": collections
        };
        fetch(window.json_url, {
            method: "post",
            body: JSON.stringify(payload)
        });
    },
    render: function() {
        var options = this.props.options.map((option) => (
            <option key={option.value} value={option.value}>{option.name}</option>
        ));
        return (
            <form onSubmit={this.handleSubmit}>
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
                <input type="submit" className="btn btn-default" disabled={!this.props.active} />
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
    doFetch: function(params) {
        if (params.length && !this.state.data.active) {
            console.log("It's over man.");
            return;
        }
        var that = this;
        if (this.state.value) {
            params += "&value=1";
        }
        if (this.state.swap_colors) {
            params += "&color=1";
        }
        if (!this.state.data.active) {
            params += "&dump=" + escape(this.state.data.dump);
        }
        fetch(window.json_url + "?code=" + escape(this.state.data.code) + params)
        .then(handle_status)
        .then(to_json)
        .then(handle_error)
        .then(
            function(data) {
                console.log(data);
                that.setState({"data": data});
                set_problem_form_state(data.problem_name, data.problem_collections, data.dump);
            }
        )
        .catch(
            function(error) {
                console.log("Request failed", error);
            }
        );
    },
    pushUndo: function() {
        if (this.state.data.active) {
            var undos = this.state.undos;
            undos.push(this.state.data.code);
            this.setState({"undos": undos});
        }
    },
    handleUndo: function() {
        var undos = this.state.undos;
        if (undos.length) {
            var code = undos.pop();
            var data = this.state.data;
            var old_code = data.code;
            data.code = code;  // Evil. Can modify props.
            var old_active = data.active;
            data.active = true;
            this.setState({
                "undos": undos,
                "data": data,
            });
            this.doFetch("");
            data.code = old_code;  // Undo the evil.
            data.active = old_active;
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
        // Have to mutate here so that doFetch works correctly.
        this.state.swap_colors = !this.state.swap_colors;
        this.setState({"swap_colors": this.state.swap_colors});
        this.doFetch("");
    },
    handleModeChange: function(mode) {
        this.setState({"mode": mode});
    },
    handleKoThreatsChange: function(value) {
        this.doFetch("&ko_threats=" + value);
    },
    handleReset: function() {
        this.setState({
            "value": false,
            "swap_colors": this.props.swap_colors,
            "data": this.props.data,
            "undos": []
        });
    },
    getInitialState: function() {
        return {
            "data": this.props.data,
            "vs_book": true,
            "value": false,
            "swap_colors": this.props.swap_colors,
            "mode": "move",
            "undos": [],
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
        if (this.state.data.value !== undefined) {
            child_results = this.state.data.value.children;
        }
        var player_title = this.state.data.white_to_play ? "White to play" : "Black to play";
        var ko_threat_choices = [];
        for (var i = this.state.data.min_ko_threats; i <= this.state.data.max_ko_threats; i++) {
            ko_threat_choices.push([i, i]);
        }
        return (
            <div className="game row">
                <div className="col-md-5">
                    <h3>{player_title}</h3>
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
                    <Button label="Undo" onClick={this.handleUndo} />
                    <Button label="Book move" onClick={this.handleBook} />
                    <ProblemForm
                        name={this.props.data.problem_name}
                        collections={this.props.data.problem_collections}
                        dump={this.props.data.dump}
                        options={this.props.problem_options}
                        active={this.state.data.active}
                    />
                </div>
                <div className="col-md-3">
                    <Button label="Swap players" onClick={this.handleSwap} />
                    <LabeledCheckBox label="Show result" checked={this.state.value} onChange={this.handleValueChange} />
                    <LabeledCheckBox label="Play against the book" checked={this.state.vs_book} onChange={this.handleVsBookChange} />
                    <LabeledCheckBox label="Swap colors" checked={this.state.swap_colors} onChange={this.handleColorChange} />
                    <InlineRadioGroup title="Ko threats:" choices={ko_threat_choices} selected={this.state.data.ko_threats} onChange={this.handleKoThreatsChange} />
                    <RadioGroup choices={mode_choices} selected={this.state.mode} onChange={this.handleModeChange} />
                    <StatsPanel data={this.state.data} />
                    <Button label="Reset" onClick={this.handleReset} />
                </div>
                <div className="col-md-4">
                    <ChildResults results={child_results} height={this.props.data.height} />
                </div>
            </div>
        );
    }
});


ReactDOM.render(
    <Game data={window.state} swap_colors={window.swap_colors} problem_options={window.problem_options} />,
    document.getElementById("container")
);
