#import "PQQuestsStore.h"

static NSString *const kKey = @"puzzlequest.quests";

@implementation PQQuestsStore

+ (instancetype)sharedStore
{
    static PQQuestsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQQuestsStore alloc] init];
    });
    return shared;
}

- (NSInteger)completed
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setCompleted:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
