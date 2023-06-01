function Step(context) {
  this._context = context;
}

Step.prototype = {
  areaStart() {
    this._areaLine = 0;
  },
  areaEnd() {
    this._areaLine = null;
  },
  lineStart() {
    if (this._areaLine !== 1) {
      this._x = null;
      this._y = null;
      this._bandwidth = null;
    }
    this._point = 0;
  },
  lineEnd() {
    if (this._areaLine === 0) {
      this._areaLine++;
    } else if (this._areaLine === 1) {
      this._context.closePath();
    }
  },
  point(x, y) {
    x = +x;
    y = +y;

    if (this._bandwidth == null && this._x != null) {
      this._bandwidth = x - this._x;
    }

    if (!this._areaLine) {
      if (this._point === 0) {
        this._context.moveTo(x, y);
      } else {
        if (this._point === 1) {
          const negX = this._x - this._bandwidth / 2;
          this._context.moveTo(negX, this._y);
        }
        const posX = this._x + this._bandwidth / 2;
        const posX2 = x + this._bandwidth / 2;
        this._context.lineTo(posX, this._y);
        this._context.lineTo(posX, y);
        this._context.lineTo(posX2, y);
      }
    }

    if (this._areaLine === 1) {
      const posX2 = (this._point === 0 ? this._x : x) + this._bandwidth / 2;
      this._context.lineTo(posX2, y);
      const posX = x - this._bandwidth / 2;
      this._context.lineTo(posX, y);
    }

    this._x = x;
    this._y = y;
    this._point++;
  },
};

window.d3_stepMiddle = function stepMiddle(context) {
  return new Step(context);
};
