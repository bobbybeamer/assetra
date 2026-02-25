import Foundation

struct ConflictAcknowledgement: Codable {
    let conflictId: String
    let resolution: String
    let resolvedAt: String

    enum CodingKeys: String, CodingKey {
        case conflictId = "conflict_id"
        case resolution
        case resolvedAt = "resolved_at"
    }
}
