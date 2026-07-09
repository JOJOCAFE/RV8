`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC922 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Fairchild MM74C922/MM74C923: `Components/Source/MM74C922.PDF` | N18A, 18-pin PDIP |
//
// ## 74HC922/MM74C922 - 16-Key Encoder, 18-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | ROW Y1 |
// | 2 | ROW Y2 |
// | 3 | ROW Y3 |
// | 4 | ROW Y4 |
// | 5 | OSCILLATOR |
// | 6 | KEYBOUNCE MASK |
// | 7 | COLUMN X4 |
// | 8 | COLUMN X3 |
// | 9 | GND |
// | 10 | COLUMN X2 |
// | 11 | COLUMN X1 |
// | 12 | DATA AVAILABLE |
// | 13 | OUTPUT ENABLE |
// | 14 | DATA OUT D |
// | 15 | DATA OUT C |
// | 16 | DATA OUT B |
// | 17 | DATA OUT A |
// | 18 | VCC |
//


// 74HC922/MM74C922: 16-key encoder behavioral model

module ttl_74hc922 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [3:0] RowY,
  output reg [3:0] ColumnX,
  input Oscillator,
  input KeybounceMask,
  input OutputEnable,
  output [3:0] DataOut,
  output DataAvailable
);

reg [1:0] scan_col;
reg [3:0] latched_code;
reg data_available;
integer row_index;

initial begin
  scan_col = 2'd0;
  ColumnX = 4'b1110;
  latched_code = 4'h0;
  data_available = 1'b0;
end

always @(posedge Oscillator) begin
  scan_col <= scan_col + 2'd1;
  ColumnX <= ~(4'b0001 << (scan_col + 2'd1));
end

always @* begin
  data_available = 1'b0;
  latched_code = {2'b00, scan_col};

  for (row_index = 0; row_index < 4; row_index = row_index + 1) begin
    if (!RowY[row_index]) begin
      data_available = 1'b1;
      latched_code = {row_index[1:0], scan_col};
    end
  end
end

assign #(DELAY_RISE, DELAY_FALL) DataAvailable = data_available & KeybounceMask;
assign #(DELAY_RISE, DELAY_FALL) DataOut = OutputEnable ? 4'hz : latched_code;

endmodule
