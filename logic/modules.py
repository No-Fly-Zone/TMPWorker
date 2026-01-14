
import io
import struct


class PalFile:
    """
    色盘
    """

    def __init__(self, filename):
        self.filename = filename
        self.palette = []
        self.load()

    def load(self):
        with open(self.filename, "rb") as f:
            data = f.read()

        if len(data) != 256 * 3:
            raise ValueError("色盘大小不正确，要求为 768 字节")

        for i in range(256):
            r6 = data[i * 3] & 0x3F
            g6 = data[i * 3 + 1] & 0x3F
            b6 = data[i * 3 + 2] & 0x3F

            # 6-bit → 8-bit 显示，最大值 252
            r8 = r6 * 252 // 63
            g8 = g6 * 252 // 63
            b8 = b6 * 252 // 63

            self.palette.append((r8, g8, b8, 255))


# class PalFile:
#     '''
#     色盘
#     调用：  PalFile.palette
#     '''

#     def __init__(self, filename):
#         self.filename = filename
#         self.palette = []
#         self.load()

#     def load(self):
#         with open(self.filename, "rb") as f:
#             data = f.read()

#         if len(data) != 256 * 3:
#             raise ValueError("色盘大小不正确，要求为 768")

#         for i in range(256):
#             r = data[i*3]
#             g = data[i*3 + 1]
#             b = data[i*3 + 2]

#             # 6bit 扩展到 8bit
#             r_8 = r * 255 // 63
#             g_8 = g * 255 // 63
#             b_8 = b * 255 // 63
#             self.palette.append((r_8, g_8, b_8, 255))

# class PalFile:
#     """
#     色盘（编辑 / 调色工具用）
#     调用：PalFile.palette
#     """

#     def __init__(self, filename):
#         self.filename = filename
#         self.palette = []
#         self.load()

#     def load(self):
#         with open(self.filename, "rb") as f:
#             data = f.read()

#         if len(data) != 256 * 3:
#             raise ValueError("色盘大小不正确，要求为 768 字节")

#         for i in range(256):
#             r6 = data[i * 3]
#             g6 = data[i * 3 + 1]
#             b6 = data[i * 3 + 2]

#             # 保证只使用低6位
#             r6 &= 0x3F
#             g6 &= 0x3F
#             b6 &= 0x3F

#             # 简单线性扩展到 8-bit（0-255）
#             r8 = r6 * 255 // 63
#             g8 = g6 * 255 // 63
#             b8 = b6 * 255 // 63

#             self.palette.append((r8, g8, b8, 255))

class TmpTile:
    '''
    特定 TMP 文件的 Tile

    参数：
        self.X, self.Y              地形块的 XY 位置
        self.ZDataOffset            Zdata 的偏移

        self.ExtraX, self.ExtraY    Extra 部分地形块的 XY 位置
        self.ExtraDataOffset        Extra 部分 Zdata 的偏移
        self.ExtraZDataOffset       Extra 部分 Zdata 的偏移
        self.ExtraWidth, self.ExtraHeight, data_flags

        HasDamagedData = 0: TMP 变体文件之一随机选取
        HasDamagedData = 1: 无 TMP 变体，这样桥块就不会随机化。
    '''

    def __init__(self):
        self.X = None
        self.Y = None
        self.ExtraDataOffset = None
        self.ZDataOffset = None
        self.ExtraZDataOffset = None
        self.ExtraX = None
        self.ExtraY = None
        self.ExtraWidth = None
        self.ExtraHeight = None
        self.DataBitfield = None
        self.Height = None
        self.TerrainType = None
        self.RampType = None
        self.RadarRedLeft = None
        self.RadarGreenLeft = None
        self.RadarBlueLeft = None
        self.RadarRedRight = None
        self.RadarGreenRight = None
        self.RadarBlueRight = None
        self.TileData = None
        self.ZData = None
        self.has_extra = None
        self.has_z = None
        self.has_damaged = None
        self.ExtraData = None
        self.ExtraZData = None

    def read(self, f, block_width, block_height):
        # read ten int32
        ints = struct.unpack("<10i", f.read(40))
        (self.X, self.Y, self.ExtraDataOffset, self.ZDataOffset,
         self.ExtraZDataOffset, self.ExtraX, self.ExtraY,
         self.ExtraWidth, self.ExtraHeight, data_flags) = ints
        self.DataBitfield = data_flags
        self.Height = struct.unpack("<B", f.read(1))[0]
        self.TerrainType = struct.unpack("<B", f.read(1))[0]
        self.RampType = struct.unpack("<B", f.read(1))[0]

        self.RadarRedLeft = struct.unpack("<B", f.read(1))[0]
        self.RadarGreenLeft = struct.unpack("<B", f.read(1))[0]
        self.RadarBlueLeft = struct.unpack("<B", f.read(1))[0]
        self.RadarRedRight = struct.unpack("<B", f.read(1))[0]
        self.RadarGreenRight = struct.unpack("<B", f.read(1))[0]
        self.RadarBlueRight = struct.unpack("<B", f.read(1))[0]

        f.read(3)  # padding

        tile_size = block_width * block_height // 2
        self.TileData = f.read(tile_size)

        # DataBitfield
        self.has_extra = (self.DataBitfield & 0x01) != 0
        self.has_z = (self.DataBitfield & 0x02) != 0
        self.has_damaged = (self.DataBitfield & 0x04) != 0

        # print(f'No_damaged: {int(self.has_damaged)} Zdata: {int(self.has_z)} Extra: {int(self.has_extra)}')

        if self.has_z:
            self.ZData = f.read(tile_size)
        else:
            self.ZData = None

        if self.has_extra:
            ext_size = abs(self.ExtraWidth * self.ExtraHeight)
            # protect against malformed header
            if ext_size > 0:
                self.ExtraData = f.read(ext_size)
            else:
                self.ExtraData = None
        else:
            self.ExtraData = None

        if self.has_extra and self.has_z and self.ExtraZDataOffset > 0:
            ext_size = abs(self.ExtraWidth * self.ExtraHeight)
            if ext_size > 0:
                self.ExtraZData = f.read(ext_size)
            else:
                self.ExtraZData = None
        else:
            self.ExtraZData = None

    def tile_to_bytes(self, block_width, block_height):
        """
        将一个 TmpTile 序列化为字节流，便于写回 TMP 文件。

        ExtraDataOffset/ZDataOffset 等不重新计算（写入原值或0），因为索引表的 offset 会指向该 tile 的开始位置来访问。
        """
        # pack ten ints (keep original offsets/values)
        ints = (
            self.X,
            self.Y,
            getattr(self, "ExtraDataOffset", 0),
            getattr(self, "ZDataOffset", 0),
            getattr(self, "ExtraZDataOffset", 0),
            self.ExtraX,
            self.ExtraY,
            self.ExtraWidth,
            self.ExtraHeight,
            self.DataBitfield
        )
        buf = io.BytesIO()
        buf.write(struct.pack("<10i", *ints))

        # single-byte fields
        buf.write(struct.pack("<B", self.Height))
        buf.write(struct.pack("<B", self.TerrainType))
        buf.write(struct.pack("<B", self.RampType))

        buf.write(struct.pack("<B", self.RadarRedLeft))
        buf.write(struct.pack("<B", self.RadarGreenLeft))
        buf.write(struct.pack("<B", self.RadarBlueLeft))
        buf.write(struct.pack("<B", self.RadarRedRight))
        buf.write(struct.pack("<B", self.RadarGreenRight))
        buf.write(struct.pack("<B", self.RadarBlueRight))

        # padding 3 bytes
        buf.write(b'\x00' * 3)

        # TileData: expected size
        tile_size = block_width * block_height // 2
        td = self.TileData
        if len(td) != tile_size:
            # protect: pad or trim
            if len(td) < tile_size:
                td = td + b'\x00' * (tile_size - len(td))
            else:
                td = td[:tile_size]
        buf.write(td)

        # ZData
        if self.has_z and self.ZData:
            zd = self.ZData
            if len(zd) != tile_size:
                if len(zd) < tile_size:
                    zd = zd + b'\x00' * (tile_size - len(zd))
                else:
                    zd = zd[:tile_size]
            buf.write(zd)

        # ExtraData
        if self.has_extra and self.ExtraData is not None:
            ext_size = abs(self.ExtraWidth * self.ExtraHeight)
            ed = self.ExtraData
            if len(ed) != ext_size:
                if len(ed) < ext_size:
                    ed = ed + b'\x00' * (ext_size - len(ed))
                else:
                    ed = ed[:ext_size]
            buf.write(ed)

        # ExtraZData
        if self.has_extra and self.has_z and self.ExtraZData:
            ext_size = abs(self.ExtraWidth * self.ExtraHeight)
            ez = self.ExtraZData
            if len(ez) != ext_size:
                if len(ez) < ext_size:
                    ez = ez + b'\x00' * (ext_size - len(ez))
                else:
                    ez = ez[:ext_size]
            buf.write(ez)

        return buf.getvalue()


class TmpFile:
    '''
    TMP 文件

    调用：  TmpFile.tiles
    '''

    def __init__(self, filename):
        self.filename = filename
        self.tiles: list[TmpTile] = []
        self.load()

    def load(self):
        with open(self.filename, "rb") as f:
            header = f.read(16)
            if len(header) < 16:
                raise ValueError("File too short or not a TMP")
            self.Width, self.Height, self.BlockWidth, self.BlockHeight = struct.unpack(
                "<4i", header)
            idx_count = self.Width * self.Height
            index_raw = f.read(idx_count * 4)
            if len(index_raw) < idx_count * 4:
                raise ValueError("Index table truncated")
            indices = struct.unpack("<" + "i" * idx_count, index_raw)

            for offset in indices:
                if offset == 0:
                    self.tiles.append(None)
                    continue

                f.seek(offset)
                tile = TmpTile()
                tile.read(f, self.BlockWidth, self.BlockHeight)
                self.tiles.append(tile)

    def compute_canvas_bounds(self):
        '''
        导出该 tmp 文件的画布大小

        :param tmp: 说明
        :type tmp: TmpFile
        '''
        half_cy = self.BlockHeight // 2
        xs = []
        ys = []
        rs = []
        bs = []
        for tile in self.tiles:

            if tile is None:
                continue
            TX = tile.X
            TY = tile.Y
            TR = TX + self.BlockWidth
            TB = TY + self.BlockHeight

            if tile.has_extra:
                TX = min(TX, tile.ExtraX)
                TY = min(TY, tile.ExtraY)
                TR = max(TR, tile.ExtraX + tile.ExtraWidth)
                TB = max(TB, tile.ExtraY + tile.ExtraHeight)

            TY -= tile.Height * half_cy
            TB -= tile.Height * half_cy

            xs.append(TX)
            ys.append(TY)
            rs.append(TR)
            bs.append(TB)

        if not xs:
            return 0, 0, 0, 0

        X = min(xs)
        Y = min(ys)
        R = max(rs)
        B = max(bs)
        return X, Y, R, B
