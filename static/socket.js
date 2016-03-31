var Proxy = Proxy || {};
(function (pr) {
	pr.INCOMING_MESSAGE_SIZE = 256;
	pr.OUTGOING_MESSAGE_SIZE = 1024;
	pr.SALT_SIZE = 16;
	pr.LENGTH_SIZE = 2;
	pr.TICK_DELAY = 5000;

	pr.current_progress = null;
	pr.expected_size = 0;
	pr.response_buffer = "";

	pr.tickTimeout = null;

	pr.socket = new WebSocket("ws://" + window.location.host + window.location.pathname + "socket");

	pr.socket.onopen = function () {
		pr.tick();
	};

	pr.socket.onmessage = function (event) {
		var data = event.data;
		var salt = data.substring(0, pr.SALT_SIZE);
		//var data_size = jspack.Unpack(">H", data.substring(pr.SALT_SIZE, pr.SALT_SIZE + pr.LENGTH_SIZE))[0];
		//console.log("d: " + data.charCodeAt(17));
		var data_size = data.charCodeAt(17) + 256*data.charCodeAt(16);

		if(data_size == 0) {
			console.log("no data");
			return;
		}
		console.log("got data of size: " + data_size);
		var data_str = data.substring(pr.SALT_SIZE + pr.LENGTH_SIZE, pr.SALT_SIZE + pr.LENGTH_SIZE + data_size);
		pr.parseData(data_str);
		
	};

	pr.socket.onclose = function () {
		console.log("rip socket");
		clearTimeout(pr.tickTimeout);
	};

	pr.parseData = function (data) {
		var data_str = "";

		if(this.current_progress === null) {
			this.current_progress = 0;
			var url_size = data.charCodeAt(0);
			var url = data.substring(1, 1 + url_size)
			var data_size = jspack.Unpack(">I", data.substring(1 + url_size, 5 + url_size));
			this.expected_size = data_size;
			data_str = data.substring(5 + url_size);
		} else {
			data_str = data;
		}

		//TODO: support for two response segments in one message
		this.response_buffer += data_str;

		if(data_str.length > this.expected_size - this.current_progress) {
			this.current_progress += data_str.length;
		} else {
			console.log("Completed fetch");
			console.log(this.response_buffer);
			this.response_buffer = "";
			this.current_progress = null;
		}
	};

	pr.buffer = {
		head: null,
		tail: null,

		push: function (url) {
			var item = {
				"url" : url,
				"prev" : this.tail,
				"next" : null
			};

			if(this.tail !== null) {
				this.tail.next = item;
			} else {
				this.head = item;
			}
		},

		isEmpty: function () {
			return this.head === null;
		},

		pop: function () {
			if(this.isEmpty()) {
				return null;
			}
			var item = this.head;
			var url = item.url;
			this.head = item.next;

			if(this.head === null) {
				this.tail = null;
			}
			return url;
		}
	};

	pr.proxyFetch = function (url) {
		this.buffer.push(url);
	};

	pr.tick = function () {
		console.log("tick");
		clearTimeout(this.tickTimeout);
		var datastr = "";

		if(!this.buffer.isEmpty()) {
			var url = this.buffer.pop();
			var data = [
				{
					"type" : "fetch",
					"url" : url
				}
			]
			//TODO: group several queued commands together if there is enough space.
			//TODO: better yet, allow commands to be split across messages
			datastr = JSON.stringify(data);
		}
		var salt = this.getSalt();
		var len = datastr.length;
		var lenbytes = jspack.Pack(">H", [len]);
		var lenstr = String.fromCharCode(lenbytes[0]) + String.fromCharCode(lenbytes[1]);
		var message_head = salt + lenstr + datastr;
		var padding = this.getPadding(this.INCOMING_MESSAGE_SIZE - message_head.length);
		var message = message_head + padding;
		this.socket.send(message);
		this.tickTimeout = setTimeout(function () {
			pr.tick();
		}, pr.TICK_DELAY);
	};

	pr.getSalt = function () {
		return Math.random().toString(36).slice(2, this.SALT_SIZE + 2);
	};

	pr.getPadding = function (length) {
		return new Array(length + 1).join("Q");
	}

})(Proxy);

