// Places people live and park, collected while the world is built, so commuters can be
// given a real house and a real parking stall at Vira.
//
// A home is { city, drive: [x, z] (where the car parks), street: z of the street it faces }.
// Only houses without a parked prop car are registered, so a commuter never shares a driveway.
export const HOMES = { saltbrush: [], halcyon: [], ironwood: [] };

// Staff parking at Vira: { x, z (stall center), aisle (z of the aisle it opens onto) }.
export const VIRA_STALLS = [];
