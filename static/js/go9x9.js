(function(){
    // Only synchronous requests make sense when updating the board, but they're getting deprecated.
    // Hack a lock instead.
    var ajax_locked = false;

    var move_num = 0;

    var undos = window.path_undos.slice();
    var redos = window.path_redos.slice();

    var coord_map = {
        "A": 0,
        "B": 1,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
        "G": 6,
        "H": 7,
        "I": 8,
        "J": 9,
        "K": 10,
        "L": 11,
        "M": 12
    };

    var game_info_structure = [
        ["black_player", "Black player"],
        ["black_rank", "Black rank"],
        ["white_player", "White player"],
        ["white_rank", "White rank"],
        ["result", "Result"],
        ["date", "Date"],
        ["handicap", "Handicap"],
        ["komi", "Komi"],
        ["game_name", "Game name"],
        ["event", "Event"],
        ["round", "Round"],
        ["place", "Place"],
        ["rules", "Rules"],
        ["time", "Game time"],
        ["overtime", "Overtime"],
        ["move_number", "Move number"],
        ["total_moves", "Number of Moves"]
    ];

    function heat_map(score){
        var rgb;
        if (score < -7){
            rgb = [0, 0, Math.pow((81 + score) / 74, 2)];
        }
        else if (score < 0){
            rgb = [0, (score + 7) / 7, -score / 7];
        }
        else if (score < 7){
            rgb = [score / 7, (7 - score) / 7, 0];
        }
        else {
            var w = 1 - Math.pow(1 - (score - 7) / 74, 2);
            rgb = [1, w, w];
        }
        return "rgb(" + (255 * rgb[0]).toFixed(0) + ", " + (255 * rgb[1]).toFixed(0) + ", " + (255 * rgb[2]).toFixed(0) + ")";
    }

    var board_color = "#db7";

    var scale = 33;
    function draw_coords(coord){
        return [scale * coord_map[coord[0]], scale * parseInt(coord.slice(1))];
    }

    function black_stone(draw, x, y){
        var stone = draw.circle(0.9 * scale).center(x, y).fill("#111");
        return stone;
    }

    function white_stone(draw, x, y){
        var stone = draw.circle(0.9 * scale).center(x, y).fill("#eee").stroke({width: 1.3, color: "#111"});
        return stone;
    }

    function ko_square(draw, x, y){
        var shape = draw.group();
        var bg = shape.rect(1.09 * scale, 1.09 * scale).center(x, y).fill(board_color);
        bg.attr({"fill-opacity": 0.7});
        var square = shape.rect(0.6 * scale, 0.6 * scale).center(x, y).fill("none");
        square.stroke({width: 2, color: "#333"});
        return shape;
    }

    function triangle(draw, x, y){
        var shape = draw.path("M -0.866 0.5 L 0 -1 L 0.866 0.5 z M 1.3 0.75 L 0 -1.5 L -1.3 0.75 z");
        var s = 0.3 * scale;
        shape.scale(s);
        shape.center(x / s, (y - 0.2 * scale) / s);
        shape.fill("#0ff");
        return shape;
    }

    var board;

    function render_playing_area(draw)
    {
        var max_x = 12 * scale;
        var max_y = 12 * scale;
        board = draw.rect(max_x + 3 * scale, max_y + 3 * scale).move(-1.5 * scale, -1.5 * scale).fill(board_color);
        var x = 0;
        $(["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N"]).each(function(_, letter){
            draw.text(letter).font({size: 0.5 * scale}).center(x, -scale);
            draw.text(letter).font({size: 0.5 * scale}).center(x, max_y + scale);
            x += scale;
        });
        var y = max_y;
        $(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]).each(function(_, number){
            draw.text(number).font({size: 0.5 * scale}).center(-scale, y);
            draw.text(number).font({size: 0.5 * scale}).center(max_x + scale, y);
            y -= scale;
        });
        for (var x = -0.5; x < 12 * scale; x += scale){
            draw.line(x, -0.5, x, 12 * scale - 0.5).stroke({
                width: 1,
                color: "#111"
            });
        }
        for (var y = -0.5; y < 12 * scale; y += scale){
            draw.line(-0.5, y, 12 * scale - 0.5, y).stroke({
                width: 1,
                color: "#111"
            });
        }
        for (var y = 3 * scale - 0.5; y < 11 * scale; y += 3 * scale){
            for (var x = 3 * scale - 0.5; x < 11 * scale; x += 3 * scale){
                draw.circle(0.15 * scale).center(x, y).fill("#111");
            }
        }
    }

    var hover_blacks = {};
    var hover_whites = {};
    var hover_triggers = {};
    function add_hovers(draw, hover_draw)
    {
        $(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]).each(function(_, x){
            $([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]).each(function(_, y){
                var coord = x + y;
                var c = draw_coords(coord);
                var stone = black_stone(draw, c[0], c[1]);
                stone.attr({"fill-opacity": 0.0, "stroke-opacity": 0.0});
                hover_blacks[coord] = stone;
                stone = white_stone(draw, c[0], c[1]);
                stone.attr({"fill-opacity": 0.0, "stroke-opacity": 0.0});
                hover_whites[coord] = stone;
                var trigger = hover_draw.rect(scale, scale).center(c[0], c[1]);
                trigger.attr({"fill-opacity": 0.0});
                hover_triggers[coord] = trigger;
            });
        });
    }

    var board_objects = {};
    var missing_objects = {};
    var ko = null;
    var hints = [];

    function add_object(draw, coord, shape){
        if (coord in board_objects){
            delete missing_objects[coord];
        }
        else {
            var c = draw_coords(coord);
            var object = shape(draw, c[0], c[1]);
            board_objects[coord] = object;
        }
    }

    function black_to_play(){
        var result = move_num % 2 == 0;
        if (window.location.search.indexOf("player=white") >= 0){
            return !result;
        }
        return result;
    }

    function set_score(data){
        var black_wins;
        var white_wins;
        if (black_to_play()){
            black_wins = data.player_wins;
            white_wins = data.opponent_wins;
        }
        else {
            black_wins = data.opponent_wins;
            white_wins = data.player_wins;
        }
        var draws = data.draws;
        if (black_wins === undefined){
            black_wins = 0;
            white_wins = 0;
            draws = 0;
        }
        var total = black_wins + white_wins + draws;
        if (total == 0){
            total = 1;
        }
        var chance = 100 * black_wins / total;
        $("#black_wins").text(chance.toFixed(1) + "% (" + black_wins + ")");
        chance = 100 * white_wins / total;
        $("#white_wins").text(chance.toFixed(1) + "% (" + white_wins + ")");
        chance = 100 * draws / total;
        $("#draws").text(chance.toFixed(1) + "% (" + draws + ")");
        var $score = $("#score");
        if ("low_score" in data && data.low_score !== null){
            if (data.low_score == data.high_score){
                var score = data.low_score
                if (!black_to_play()){
                    score = -score;
                }
                if (score >= 0){
                    $score.text("B+" + score);
                }
                else {
                    $score.text("W+" + (-score));
                }
            }
            else {
                var low = data.low_score;
                var high = data.high_score;
                if (!black_to_play()){
                    var temp = low;
                    low = -high;
                    high = -temp;
                }
                if (low >= 0){
                    low = "+" + low;
                }
                if (high >= 0){
                    high = "+" + high;
                }
                $score.text("From B" + low + " to B" + high + ", depending on super-ko rules.");
            }
        }
        else {
            $score.text("unknown");
        }
    }

    var game_num = 0;
    var game_id = null;
    var game_next_data = null;
    var game_previous_data = null;

    function set_game_info(data){
        $game_info = $("#game_info");
        $previous_game = $("#previous_game");
        $next_game = $("#next_game");
        $game_number = $("#game_number");
        $total_games = $("#total_games");
        $game_points = $("#game_points");
        $game_next = $("#game_next");
        $game_previous = $("#game_previous");
        $game_end = $("#game_end");
        $game_start = $("#game_start");
        $game_info.empty();

        if (data){
            game_num = data.game_num;
            $previous_game.prop("disabled", game_num == 0);
            $game_number.text(game_num + 1);
            $total_games.text(data.total_games);
            $next_game.prop("disabled", game_num + 1 >= data.total_games);
            $game_points.text(data.points);
            $(game_info_structure).each(function(_, kn){
                var key = kn[0];
                var name = kn[1];
                var value = data[key];
                if (String(value).length){
                    var $tr = $("<tr>");
                    var $td = $("<td>");
                    $td.html(name + ": " + value);
                    $tr.append($td);
                    $game_info.append($tr);
                }
            });
            game_id = data.pk;
            if ("next" in data){
                $game_next.prop("disabled", false);
                game_next_data = data.next;
            }
            else {
                $game_next.prop("disabled", true);
                game_next_data = null;
            }
            if ("previous" in data){
                $game_previous.prop("disabled", false);
                game_previous_data = data.previous;
            }
            else {
                $game_previous.prop("disabled", true);
                game_previous_data = null;
            }
            $game_end.prop("disabled", false);
            $game_start.attr("href", window.empty_url + "?game_id=" + game_id);
        }
        else {
            game_id = null;
            $previous_game.prop("disabled", true);
            $game_number.text(0);
            $total_games.text(0);
            $next_game.prop("disabled", true);
            $game_next.prop("disabled", true);
            game_next_data = null;
            $game_previous.prop("disabled", true);
            game_previous_data = null;
            $game_end.prop("disabled", true);
        }
    }

    function render_stones(draw, hint_draw, data){
        var player, opponent, hover_players, hover_opponents;
        if (black_to_play()){
            player = black_stone;
            opponent = white_stone;
            hover_players = hover_blacks;
            hover_opponents = hover_whites;
        }
        else {
            player = white_stone;
            opponent = black_stone;
            hover_players = hover_whites;
            hover_opponents = hover_blacks;
        }
        if (ko !== null){
            ko.remove();
            ko = null;
        }
        missing_objects = {};
        $.each(board_objects, function(coord, object){
            missing_objects[coord] = object;
        });
        $(data.player).each(function(_, coord){
            add_object(draw, coord, player);
        });
        $(data.opponent).each(function(_, coord){
            add_object(draw, coord, opponent);
        });
        $(data.ko).each(function(_, coord){
            var c = draw_coords(coord);
            ko = ko_square(draw, c[0], c[1]);
        });
        $.each(missing_objects, function(coord, object){
            delete board_objects[coord];
            object.remove();
        });
        var $pass = $("#pass");
        $(hints).each(function(_, object){
            object.remove();
        });
        hints = [];
        var $status = $("#status");
        var $statistics = $("#statistics");
        $statistics.empty();
        var $stats_row;
        var $win_statistics = $("#win_statistics");
        $win_statistics.empty();
        game_num = 0;
        set_game_info(data.info);
        var $next = $("#next");
        var next_found = false;
        $next.off("click");
        if (redos.length){
            $next.click(function(event){
                event.preventDefault();
                if (ajax_locked){
                    return;
                }
                ajax_locked = true;
                if ($(this).prop("disabled")){
                    return;
                }
                undos.push(current_data.endgame);
                $status.empty();
                move_num += 1;
                next_endgame({"endgame": redos.pop()});
                $(".vote").attr("disabled", false);
            });
            next_found = true;
        }
        $pass.off("click");
        $pass.prop("disabled", true);
        var label_index = 0;
        var moves = data.moves;

        $.each(hover_triggers, function(_, trigger){
            trigger.off();  // Doesn't seem to work.
            trigger.mouseover(function(){});
            trigger.mouseout(function(){});
            trigger.click(function(){});
        });

        $.each(hover_players, function(_, stone){
            stone.attr({"fill-opacity": 0.0, "stroke-opacity": 0.0});
        });
        $.each(hover_opponents, function(_, stone){
            stone.attr({"fill-opacity": 0.0, "stroke-opacity": 0.0});
        });


        $(moves).each(function(index, move_data){
            var make_move = function(event){
                event.preventDefault();
                if (ajax_locked){
                    return;
                }
                ajax_locked = true;
                if ($(this).prop("disabled")){
                    return;
                }
                redos = [];
                undos.push(data.endgame);
                $status.empty();
                move_num += 1;
                next_endgame(move_data);
                $(".vote").attr("disabled", false);
            }
            if (!next_found && (move_data.color || move_data.label)){
                $next.click(make_move);
                next_found = true;
            }
            if (move_data.label){
                if (label_index % 2 == 0){
                    $stats_row = $("<tr>");
                }
                var $td = $('<td width="5%">');
                $td.text(move_data.label)
                $td.addClass("noselect");
                $td.css("cursor", "pointer");
                $td.hover(
                    function(){
                        $(this).addClass("active");
                    },
                    function(){
                        $(this).removeClass("active");
                    }
                );
                $td.click(make_move);
                $stats_row.append($td);
                $td = $('<td width="45%">');
                $td.text((100 * move_data.likelyhood).toFixed(1) + "% (" + move_data.times_played + ")");
                $stats_row.append($td);
                if (label_index % 2 == 0){
                    $statistics.append($stats_row);
                }
                label_index += 1;

                var $tr = $("<tr>");
                $td = $("<td>");
                $td.text(move_data.label);
                $tr.append($td);
                var black_wins;
                var white_wins;
                if (black_to_play()){
                    black_wins = move_data.player_wins;
                    white_wins = move_data.opponent_wins;
                }
                else {
                    black_wins = move_data.opponent_wins;
                    white_wins = move_data.player_wins;
                }
                var draws = move_data.draws;
                var total = black_wins + white_wins + draws;
                if (total == 0){
                    total = 1;
                }
                $td = $("<td>");
                var chance = 100 * black_wins / total;
                $td.text(chance.toFixed(1) + "% (" + black_wins + ")");
                $tr.append($td);
                $td = $("<td>");
                chance = 100 * white_wins / total;
                $td.text(chance.toFixed(1) + "% (" + white_wins + ")");
                $tr.append($td);
                $td = $("<td>");
                chance = 100 * draws / total;
                $td.text(chance.toFixed(1) + "% (" + draws + ")");
                $tr.append($td);
                $td = $("<td>");
                var score;
                var low_score = move_data.low_score;
                var high_score = move_data.high_score;
                if (low_score !== null && low_score !== undefined){
                    if (black_to_play()){
                        var temp = low_score;
                        low_score = -high_score;
                        high_score = -temp;
                    }
                    if (low_score == high_score){
                        if (low_score >= 0){
                            score = "B+" + low_score;
                        }
                        else {
                            score = "W+" + (-low_score);
                        }
                    }
                    else {
                        if (low_score >= 0){
                            low_score = "+" + low_score;
                        }
                        if (high_score >= 0){
                            high_score = "+" + high_score;
                        }
                        score = "B" + low_score + " to B" + high_score;
                    }
                }
                else {
                    score = "?";
                }
                $td.text(score);
                $tr.append($td);
                $win_statistics.append($tr);
            }
            var coord = move_data.coord;
            if (coord == "pass"){
                $pass.prop("disabled", false);
                $pass.click(make_move);
                return;
            }
            var trigger = hover_triggers[coord];
            var stone = hover_players[coord];
            trigger.mouseover(function(){
                stone.attr({"fill-opacity": 0.5, "stroke-opacity": 0.5});
            });
            trigger.mouseout(function(){
                stone.attr({"fill-opacity": 0.0, "stroke-opacity": 0.0});
            });
            trigger.click(make_move);
            var c = draw_coords(coord);
            if (move_data.color){
                var hint = hint_draw.rect(0.9 * scale, 0.9 * scale).center(c[0], c[1]);
                hint.fill(move_data.color).attr({"fill-opacity": 0.5});
                hints.push(hint);
            }
            if (move_data.label){
                var label = draw.text(move_data.label).font({size: 0.7 * scale}).center(c[0], c[1]).fill("#eee");
                hints.push(label);
            }
            /*
            var val = move_data.heuristic_value;
            if (val !== null && val !== undefined){
                var hint = hint_draw.rect(1.0 * scale, 1.0 * scale).center(c[0], c[1]);
                hint.fill(heat_map(-move_data.heuristic_value));
                hint.attr({"fill-opacity": 0.75});
                hints.push(hint);
            }
            */
        });
    }

    var background_draw;
    var midground_draw;
    var foreground_draw;
    var hover_draw;

    function render_board(data){
        var svg = SVG("board");
        var draw = svg.group();
        background_draw = draw.nested();
        midground_draw = draw.nested();
        foreground_draw = draw.nested();
        hover_draw = draw.nested();
        render_playing_area(background_draw);
        add_hovers(foreground_draw, hover_draw);
        set_position(data);
        draw.move(-board.x(), -board.y());
        svg.size(board.width(), board.height());
        svg.addClass("center-block");
    }

    function set_position(data){
        render_stones(foreground_draw, midground_draw, data);
        set_score(data);
        set_messages(data.messages);
        var $status = $("#status");
        var $resolve = $("#resolve");
        var $permalink = $("#permalink");
        var $undo = $("#undo");
        if (data.passes == 1){
            $status.text("The opponent passed.");
        }
        else if (data.passes == 2){
            $status.text("The game has ended.");
            $resolve.prop("disabled", false);
        }
        else {
            $status.empty();
        }
        var parts = window.link_url.split("/");
        parts[parts.length - 2] = current_data.endgame;
        var url = parts.join("/");
        if (!black_to_play()){
            url += "?player=white";
        }
        $permalink.attr("href", url);
        $undo.prop("disabled", undos.length == 0);
    }

    function next_endgame(move_data, game_pk){
        var parts = window.json_url.split("/");
        parts[parts.length - 2] = move_data.endgame;
        var url = parts.join("/");
        url += "?sort=" + $("#sort").val();
        if (!black_to_play()){
            url += "&player=white";
        }
        if (game_pk !== undefined){
            url += "&game_id=" + game_pk;
        }
        var $vote_buttons = $(".vote")
        $vote_buttons.attr("disabled", true);
        var $resolve = $("#resolve");
        $resolve.prop("disabled", true);
        $.ajax({
            url: url,
            dataType: "json",
            async: true,
            success: function(data){
                if (data.status != "OK"){
                    return;
                }
                current_data = data;
                set_position(data);
                set_vote_labels(move_data);
                ajax_locked = false;
            }
        });
    }

    function set_vote_labels(data){
        $(".votes input").each(function(){
            var $this = $(this);
            var name = $this.val();
            var num = data[name];
            if (num){
                num = " (" + num + ")";
            }
            else {
                num = "";
            }
            $this.siblings("span").text(num);
            var $label = $this.parent();
            $label.removeClass("active");
            if (data.user_vote == name){
                $label.addClass("active");
            }
        });
    }

    function set_messages(data){
        var $messages = $("#messages");
        $messages.empty();
        $(data).each(function(_, message){
            var $blockquote = $("<blockquote>");
            $blockquote.addClass("message");
            var $span = $("<span>");
            $span.addClass("glyphicon glyphicon-trash pull-right message-action");
            $span.attr("aria-hidden", true);
            $span.attr("data-toggle", "tooltip");
            $span.attr("data-placement", "bottom");
            $span.data("pk", message.pk);
            if (message.editable){
                $span.addClass("glyphicon-trash");
                $span.attr("title", "Delete");
                $span.data("action", "delete");
            }
            else {
                $span.addClass("glyphicon-flag");
                $span.attr("title", "Flag as inappropriate");
                $span.data("action", "flag");
            }
            $span.tooltip();
            $span.show();
            $span.fadeTo(0, 0);
            $blockquote.append($span);
            var $p = $("<p>");
            $p.html(message.content);
            $blockquote.append($p);
            var $footer = $("<footer>");
            var $strong = $("<strong>");
            $strong.text(message.user);
            $footer.append($strong);
            $footer.append(" on " + message.date);
            $blockquote.append($footer);
            $messages.append($blockquote);
        });
        $(".message").hover(
            function(){
                var $this = $(this);
                $this.addClass("active");
                $this.children(".message-action").fadeTo("fast", 1);
            },
            function(){
                var $this = $(this);
                $this.removeClass("active");
                $this.children(".message-action").fadeTo("fast", 0);
            }
        );
        $(".message-coord").each(function(_, mc){
            var $mc = $(mc);
            var coord = $mc.text().replace("J", "I");
            coord = coord[0] + (9 - coord[1]);
            c = draw_coords(coord);
            var mark = triangle(foreground_draw, c[0], c[1]);
            mark.attr("fill-opacity", 0.0);
            $mc.hover(
                function(){
                    mark.attr("fill-opacity", 0.9);
                },
                function(){
                    mark.attr("fill-opacity", 0.0);
                }
            );
        });
        $(".message-action").click(function(){
            var $this = $(this);
            var data = {
                "message_action": $this.data("action"),
                "pk": $this.data("pk"),
                "state": current_data.endgame,
                "black_to_play": black_to_play()
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                function(data) {
                    set_messages(data);
                },
                "json"
            );
        });
    }

    var current_data;
    $(document).ready(function(){
        $(document).keydown(function(event){
            if ($("#comment_box").is(":focus")){
                return;
            }
            // Arrow keys
            if (event.keyCode == 37 || event.keyCode == 39){
                var prev;
                var next;
                if ($("#game_tab_label").hasClass("active")){
                    prev = $("#game_previous");
                    if (prev.prop("disabled")){
                        prev = $("#undo");
                    }
                    next = $("#game_next");
                    if (next.prop("disabled")){
                        next = $("#next");
                    }
                }
                else {
                    prev = $("#undo");
                    next = $("#next");
                }
                if (event.keyCode == 37){
                    prev.click();
                }
                else {
                    next.click();
                }
            }
            // Space
            if (event.keyCode == 32){
                $("#pass").click();
            }
        });
        $("#undo").click(function(){
            if (ajax_locked){
                return;
            }
            ajax_locked = true;
            if (undos.length){
                move_num -= 1;
                redos.push(current_data.endgame);
                next_endgame({"endgame": undos.pop()});
            }
        });
        $(".vote").click(function(){
            var $this = $(this);
            // Labels don't seem to respect the disabled property.
            if ($this.attr("disabled")){
                return;
            }
            var $input = $this.children("input");
            var name = $input.val();
            var data = {
                "type": name,
                "source": undos[undos.length - 1],
                "target": current_data.endgame
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                set_vote_labels,
                "json"
            );
        });
        $("#resolve").click(function(){
            if (!confirm("Are you sure you want to resolve this position?\nAll stones will be considered alive.")){
                return;
            }
            $("#resolve").prop("disabled", true);
            var history = undos.slice();
            history.push(current_data.endgame);
            var data = {
                "resolve": history
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                function(data) {
                    set_score(data);
                },
                "json"
            );
        });
        function go_to_end(game_pk){
            var parts = window.end_json_url.split("/");
            parts[parts.length - 2] = current_data.endgame;
            var url = parts.join("/");
            if (game_pk !== undefined){
                url += "?game_id=" + game_pk;
            }
            $.ajax({
                url: url,
                dataType: "json",
                async: true,
                success: function(data){
                    if (data.length){
                        move_num += data.length;
                        undos.push(current_data.endgame);
                        redos = [];
                        $.merge(undos, data.slice(0, data.length - 1));
                        // Clear the board. Color changing objects are a pain.
                        $.each(board_objects, function(coord, object){
                            delete board_objects[coord];
                            object.remove();
                        });
                        next_endgame({"endgame": data[data.length - 1]});
                    }
                }
            });
        }
        $("#end").click(function(){
            if (ajax_locked){
                return;
            }
            ajax_locked = true;
            go_to_end();
        });
        $("#game_end").click(function(){
            if (ajax_locked){
                return;
            }
            ajax_locked = true;
            go_to_end(game_id);
        });
        function change_game(){
            var parts = window.game_json_url.split("/");
            parts[parts.length - 3] = current_data.endgame;
            parts[parts.length - 2] = game_num;
            var url = parts.join("/");
            url += "?sort=" + $("#sort").val();
            $.ajax({
                url: url,
                dataType: "json",
                success: function(data){
                    set_game_info(data);
                }
            });
        };
        $("#next_game").click(function(){
            game_num += 1;
            change_game();
        });
        $("#previous_game").click(function(){
            game_num -= 1;
            change_game();
        });
        function vote_game(type){
            if (game_id === null){
                return;
            }
            var data = {
                "type": type,
                "game_id": game_id
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                function(points){
                    $("#game_points").text(points);
                },
                "json"
            );
        }
        $("#game_next").click(function(event){
            event.preventDefault();
            if (ajax_locked){
                return;
            }
            ajax_locked = true;
            if ($(this).prop("disabled")){
                return;
            }
            undos.push(current_data.endgame);
            redos = [];
            $("#status").empty();
            move_num += 1;
            next_endgame(game_next_data, game_id);
            $(".vote").attr("disabled", false);
        });
        $("#game_previous").click(function(){
            if (ajax_locked){
                return;
            }
            ajax_locked = true;
            if ($(this).prop("disabled")){
                return;
            }
            undos = [];
            redos = []
            move_num -= 1;
            next_endgame(game_previous_data, game_id);
        });
        // TODO: Fix ordering bug when voting while sorting by popularity,
        $("#game_upvote").click(function(e){
            e.preventDefault();
            vote_game("upvote");
        });
        $("#game_downvote").click(function(e){
            e.preventDefault();
            vote_game("downvote");
        });
        $("#sort").change(function(){
            game_num = 0;
            change_game();
        });
        var $comment_box = $("#comment_box");
        $comment_box.focus(function(){
            $(this).attr("rows", 5);
            $("#comment_submit").removeClass("hidden");
        });
        $("#comment_form").submit(function(e){
            e.preventDefault();
            var message = $comment_box.val();
            if (!message.length){
                return;
            }
            var data = {
                "message": message,
                "state": current_data.endgame,
                "black_to_play": black_to_play()
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                function(data) {
                    $comment_box.val("");
                    set_messages(data);
                },
                "json"
            );
        });
        $("#create_path").click(function(){
            var data = {
                "path": true,
                "state": current_data.endgame,
                "undos": undos,
                "redos": redos,
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                function(data) {
                    $path_link = $("#path_link");
                    $path_link.empty();
                    $a = $("<a>");
                    var href = window.empty_url + "?path_id=" + data.path_id;
                    if (!black_to_play()){
                        href += "&player=white";
                    }
                    $a.attr("href", href);
                    $a.text("Link");
                    $path_link.append($a);
                },
                "json"
            );
        });
        var url = window.json_url;
        if (window.original_game_id){
            url += "?game_id=" + window.original_game_id
        }
        $.ajax({
            url: url,
            dataType: "json",
            success: function(data){
                //console.log(data);
                if (data.status != "OK"){
                    return;
                }
                current_data = data;
                render_board(data);
            }
        });
    });
})();
