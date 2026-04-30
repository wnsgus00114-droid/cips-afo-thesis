# A.F.O Unified Memory Map (H3: HBM + HBF)

Address width: 52-bit physical unified address

Physical placement convention:
- Layer 1 (bottom): compute
- Layer 2 (top): memory
- Layer-2 memory geometry: inner HBM rectangular ring + outer HBF rectangular ring

## 1. Region Table

| Prefix `[51:48]` | Start | End | Target | Notes |
|---|---|---|---|---|
| `0x0` | `0x0000_0000_0000` | `0x0FFF_FFFF_FFFF` | HBF | Dense weights (RO) |
| `0x1` | `0x1000_0000_0000` | `0x1FFF_FFFF_FFFF` | HBF | Expert weights (RO) |
| `0x2` | `0x2000_0000_0000` | `0x2FFF_FFFF_FFFF` | HBF | Shared KV chunks (RO) |
| `0x3` | `0x3000_0000_0000` | `0x3FFF_FFFF_FFFF` | HBF | Cold KV spill |
| `0x8` | `0x8000_0000_0000` | `0x8FFF_FFFF_FFFF` | HBM | Runtime KV hot |
| `0x9` | `0x9000_0000_0000` | `0x9FFF_FFFF_FFFF` | HBM | Activations |
| `0xA` | `0xA000_0000_0000` | `0xAFFF_FFFF_FFFF` | HBM | Runtime KV warm |
| `0xB` | `0xB000_0000_0000` | `0xBFFF_FFFF_FFFF` | HBM | Routing metadata cache |
| `0xF` | `0xF000_0000_0000` | `0xF000_2FFF_FFFF` | SRAM | On-die SRAM aperture |

## 2. HBM Sub-region layout (`0x8`)

| Offset | Size | Purpose |
|---|---:|---|
| `+0 GB` | 64 GB | per-request runtime KV append arena |
| `+64 GB` | 32 GB | runtime KV compaction area |
| `+96 GB` | 16 GB | hot shared KV replicas |
| `+112 GB` | 8 GB | runtime page tables / indirection |
| `+120 GB` | 8 GB | eviction log + replay buffer |

## 3. HBF Sub-region layout (`0x2` shared KV)

Chunk format:
- header: 64 B (chunk id, layer id, expert id, head group, token range, checksum)
- payload: `chunk_size` (64 KB, 128 KB, 256 KB selectable)

Placement rule:
- `stack_group = expert_id mod 4`
- `die_lane = layer_id mod lanes_per_group`
- sequential chunk ids are striped at 4 KB granularity for bandwidth leveling

## 4. SRAM Logical Regions (`0xF`)

| SRAM logical region | Size | Bank IDs |
|---|---:|---|
| WEIGHT_BUF_A | 192 MB | 0-7 |
| WEIGHT_BUF_B | 192 MB | 8-15 |
| KV_BUF_A | 96 MB | 16-19 |
| KV_BUF_B | 96 MB | 20-23 |
| ACT_RING | 96 MB | 24-27 |
| META_BUF | 32 MB | 28 |
| LHB | 64 MB | 29-31 |

## 5. Address Decoder Pseudocode
```text
if prefix in {0x0,0x1,0x2,0x3}: route = HBF
elif prefix in {0x8,0x9,0xA,0xB}: route = HBM
elif prefix == 0xF: route = SRAM
else: fault = DECODER_RANGE_ERROR
```

## 6. DMA QoS classes
- `Q0` urgent: LHB emergency refill, runtime KV critical path
- `Q1` critical: next-layer weight/KV prefetch
- `Q2` bulk: cold KV migration and background warming

## 7. ECC and Protection
- SRAM: SECDED per 256-bit line
- HBM/HBF path: end-to-end CRC32 per burst
- immutable region lock for RO regions (`0x0-0x2`) at runtime boot
